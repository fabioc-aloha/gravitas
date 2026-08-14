import json
import os
from pathlib import Path
from urllib.parse import quote

from .service import LocalRenderService, RenderJob


class AzureRenderWorker:
    """Queue/Blob adapter around the local renderer used by the worker container."""

    def __init__(
        self,
        connection_string: str,
        queue_name: str,
        container_name: str,
        output_directory: Path,
        public_base_url: str | None = None,
    ) -> None:
        from azure.storage.blob import BlobServiceClient
        from azure.storage.queue import QueueServiceClient

        self._container = BlobServiceClient.from_connection_string(
            connection_string
        ).get_container_client(container_name)
        self._queue = QueueServiceClient.from_connection_string(
            connection_string
        ).get_queue_client(queue_name)
        self._renderer = LocalRenderService(output_directory)
        self._public_base_url = public_base_url.rstrip("/") if public_base_url else None

    @classmethod
    def from_environment(cls) -> "AzureRenderWorker":
        required = ("AZURE_STORAGE_CONNECTION_STRING", "RENDER_QUEUE_NAME", "RENDER_BLOB_CONTAINER")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise ValueError(f"Missing Azure render configuration: {', '.join(missing)}.")
        return cls(
            os.environ["AZURE_STORAGE_CONNECTION_STRING"],
            os.environ["RENDER_QUEUE_NAME"],
            os.environ["RENDER_BLOB_CONTAINER"],
            Path(os.getenv("RENDER_OUTPUT_DIRECTORY", "/app/output")),
            os.getenv("RENDER_PUBLIC_BASE_URL"),
        )

    def run_once(self, visibility_timeout: int = 300) -> bool:
        message = next(
            iter(self._queue.receive_messages(messages_per_page=1, visibility_timeout=visibility_timeout)),
            None,
        )
        if message is None:
            return False
        job_blob = self._container.get_blob_client(f"jobs/{message.content}.json")
        job = json.loads(job_blob.download_blob().readall())
        job["status"] = "rendering"
        job_blob.upload_blob(json.dumps(job), overwrite=True)
        try:
            request = job["request"]
            outputs = self._renderer.render(
                RenderJob(message.content, request["mass"], request["field_of_view"])
            )
            urls = []
            for output in outputs:
                blob = self._container.get_blob_client(f"renders/{output.name}")
                with output.open("rb") as stream:
                    blob.upload_blob(stream, overwrite=True, content_type="image/png")
                urls.append(
                    f"{self._public_base_url}/renders/{quote(output.name)}"
                    if self._public_base_url
                    else blob.url
                )
            job["status"] = "complete"
            job["output_urls"] = urls
            job_blob.upload_blob(json.dumps(job), overwrite=True)
            self._queue.delete_message(message)
        except Exception:
            job["status"] = "failed"
            job_blob.upload_blob(json.dumps(job), overwrite=True)
            raise
        return True
