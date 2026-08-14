import json
import os
from pathlib import Path

from azure.core.exceptions import AzureError
from azure.storage.blob import ContentSettings

from .service import LocalRenderService, render_job_from_request


class AzureRenderWorker:
    """Queue/Blob adapter around the local renderer used by the worker container."""

    def __init__(
        self,
        connection_string: str,
        queue_name: str,
        container_name: str,
        output_directory: Path,
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
        job_id = str(job["job_id"])
        if job_id != message.content:
            raise ValueError("Queue message job ID does not match persisted job.")
        job["status"] = "rendering"
        job_blob.upload_blob(json.dumps(job), overwrite=True)
        try:
            request = job["request"]
            render_job = render_job_from_request(job_id, request)
            outputs = self._renderer.render(render_job)
            output_blob_names = []
            for output in outputs:
                blob_name = f"renders/{output.name}"
                blob = self._container.get_blob_client(blob_name)
                with output.open("rb") as stream:
                    blob.upload_blob(
                        stream,
                        overwrite=True,
                        content_settings=ContentSettings(content_type="image/png"),
                    )
                output_blob_names.append(blob_name)
            metadata_blob_name = f"renders/gravitas-{job_id}.metadata.json"
            metadata = {
                "job_id": job_id,
                "request": render_job.provenance,
                "approximations": {
                    "orbit_degrees": "screen-space disk azimuth rotation",
                    "flow_direction": "Doppler-beaming direction only",
                    "blue_spectrum": "artistic disk palette",
                    "spin": "Doppler-strength proxy; not Kerr physics",
                },
                "provenance_only": [
                    "background",
                    "disk_thickness",
                    "jet_strength",
                    "magnetic_state",
                    "observing_band",
                ],
            }
            self._container.get_blob_client(metadata_blob_name).upload_blob(
                json.dumps(metadata),
                overwrite=True,
                content_settings=ContentSettings(content_type="application/json"),
            )
            job["status"] = "complete"
            job["output_blob_names"] = output_blob_names
            job["metadata_blob_name"] = metadata_blob_name
            job_blob.upload_blob(json.dumps(job), overwrite=True)
            self._queue.delete_message(message)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            job["status"] = "failed"
            job["failure_reason"] = str(error)
            job_blob.upload_blob(json.dumps(job), overwrite=True)
            self._queue.delete_message(message)
            return True
        except (AzureError, OSError):
            raise
        return True
