import json
import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from .models import RenderRequest


class RenderStatus(StrEnum):
    QUEUED = "queued"
    RENDERING = "rendering"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class RenderJob:
    job_id: str
    request: RenderRequest
    status: RenderStatus = RenderStatus.QUEUED
    output_urls: list[str] = field(default_factory=list)

    @classmethod
    def new(cls, mass: float, field_of_view: float) -> "RenderJob":
        return cls(str(uuid4()), RenderRequest(mass=mass, field_of_view=field_of_view))

    def to_dict(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "request": self.request.model_dump(),
            "status": self.status,
            "output_urls": self.output_urls,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "RenderJob":
        return cls(
            job_id=str(value["job_id"]),
            request=RenderRequest.model_validate(value["request"]),
            status=RenderStatus(value["status"]),
            output_urls=list(value.get("output_urls", [])),
        )


class JobStore(Protocol):
    def create(self, job: RenderJob) -> None: ...

    def get(self, job_id: str) -> RenderJob | None: ...

    def update(
        self, job_id: str, *, status: RenderStatus, output_urls: list[str] | None = None
    ) -> None: ...


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, RenderJob] = {}

    def create(self, job: RenderJob) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> RenderJob | None:
        return self._jobs.get(job_id)

    def update(
        self, job_id: str, *, status: RenderStatus, output_urls: list[str] | None = None
    ) -> None:
        job = self._jobs[job_id]
        job.status = status
        if output_urls is not None:
            job.output_urls = output_urls


class AzureQueueBlobJobStore:
    """Persist jobs in Blob Storage and send job IDs through Azure Queue Storage."""

    def __init__(self, connection_string: str, queue_name: str, container_name: str) -> None:
        from azure.storage.blob import BlobServiceClient
        from azure.storage.queue import QueueServiceClient

        self._container = BlobServiceClient.from_connection_string(
            connection_string
        ).get_container_client(container_name)
        self._queue = QueueServiceClient.from_connection_string(
            connection_string
        ).get_queue_client(queue_name)

    def _blob(self, job_id: str):
        return self._container.get_blob_client(f"jobs/{job_id}.json")

    def create(self, job: RenderJob) -> None:
        self._blob(job.job_id).upload_blob(json.dumps(job.to_dict()), overwrite=False)
        self._queue.send_message(job.job_id)

    def get(self, job_id: str) -> RenderJob | None:
        try:
            payload = self._blob(job_id).download_blob().readall()
        except Exception as error:
            if error.__class__.__name__ == "ResourceNotFoundError":
                return None
            raise
        return RenderJob.from_dict(json.loads(payload))

    def update(
        self, job_id: str, *, status: RenderStatus, output_urls: list[str] | None = None
    ) -> None:
        job = self.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job.status = status
        if output_urls is not None:
            job.output_urls = output_urls
        self._blob(job_id).upload_blob(json.dumps(job.to_dict()), overwrite=True)


def job_store_from_environment() -> JobStore:
    if os.getenv("RENDER_JOB_STORE", "memory").lower() == "memory":
        return InMemoryJobStore()
    if os.getenv("RENDER_JOB_STORE", "").lower() != "azure":
        raise ValueError("RENDER_JOB_STORE must be 'memory' or 'azure'.")

    required = ("AZURE_STORAGE_CONNECTION_STRING", "RENDER_QUEUE_NAME", "RENDER_BLOB_CONTAINER")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing Azure render configuration: {', '.join(missing)}.")
    return AzureQueueBlobJobStore(
        os.environ["AZURE_STORAGE_CONNECTION_STRING"],
        os.environ["RENDER_QUEUE_NAME"],
        os.environ["RENDER_BLOB_CONTAINER"],
    )
