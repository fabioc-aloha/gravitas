import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from collections.abc import Iterable
from threading import Lock
from typing import Protocol
from uuid import uuid4

from azure.core import MatchConditions
from azure.core.exceptions import (
    ResourceExistsError,
    ResourceModifiedError,
    ResourceNotFoundError,
)

from .models import RenderRequest


CURRENT_SCHEMA_VERSION = 4
LEGACY_REQUEST_DEFAULTS: dict[str, object] = {
    "axis_inclination_degrees": 30,
    "background": "deep-space",
    "blue_spectrum": False,
    "disk_thickness": 0.1,
    "disk_temperature": 25_000_000,
    "emissivity_slope": 3,
    "flow_direction": "prograde",
    "inner_disk_radius": 6,
    "jet_strength": 0,
    "magnetic_state": "sane",
    "observing_band": "230-ghz",
    "orbit_degrees": 0,
    "seed": 0,
    "spin": 0,
}


class RenderStatus(StrEnum):
    QUEUED = "queued"
    RENDERING = "rendering"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class RenderJob:
    job_id: str
    request: RenderRequest
    owner_id: str | None = None
    status: RenderStatus = RenderStatus.QUEUED
    output_blob_names: list[str] = field(default_factory=list)
    metadata_blob_name: str | None = None

    @classmethod
    def new(cls, request: RenderRequest, *, owner_id: str | None = None) -> "RenderJob":
        return cls(str(uuid4()), request, owner_id)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "job_id": self.job_id,
            "owner_id": self.owner_id,
            "request": self.request.model_dump(),
            "status": self.status,
            "output_blob_names": self.output_blob_names,
            "metadata_blob_name": self.metadata_blob_name,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "RenderJob":
        schema_version = int(value.get("schema_version", 1))
        request_value = dict(value["request"])
        persisted_fov = request_value.pop("field_of_view", None)
        is_legacy = "axis_inclination_degrees" not in request_value
        if is_legacy:
            if persisted_fov is None or float(persisted_fov) <= 0:
                raise ValueError("Legacy render job requires a positive field_of_view.")
            request_value = LEGACY_REQUEST_DEFAULTS | request_value
            request_value["zoom"] = max(0.5, min(3.0, 20.0 / float(persisted_fov)))
        request = RenderRequest.model_validate(request_value)
        if (
            schema_version >= CURRENT_SCHEMA_VERSION
            and persisted_fov is not None
            and float(persisted_fov) != request.field_of_view
        ):
            raise ValueError("Persisted field_of_view does not match zoom.")
        return cls(
            job_id=str(value["job_id"]),
            request=request,
            owner_id=str(value["owner_id"]) if value.get("owner_id") else None,
            status=RenderStatus(value["status"]),
            output_blob_names=list(value.get("output_blob_names", [])),
            metadata_blob_name=(
                str(value["metadata_blob_name"]) if value.get("metadata_blob_name") else None
            ),
        )


class JobStore(Protocol):
    def create(self, job: RenderJob) -> None: ...

    def get(self, job_id: str) -> RenderJob | None: ...

    def update(
        self,
        job_id: str,
        *,
        status: RenderStatus,
        output_blob_names: list[str] | None = None,
    ) -> None: ...


class QuotaStore(Protocol):
    def consume(self, subject: str, window: str, limit: int) -> bool: ...


class InMemoryQuotaStore:
    def __init__(self) -> None:
        self._counts: dict[tuple[str, str], int] = defaultdict(int)
        self._lock = Lock()

    def consume(self, subject: str, window: str, limit: int) -> bool:
        if limit <= 0:
            return False
        key = (subject, window)
        with self._lock:
            if self._counts[key] >= limit:
                return False
            self._counts[key] += 1
            return True


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, RenderJob] = {}

    def create(self, job: RenderJob) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> RenderJob | None:
        return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: RenderStatus,
        output_blob_names: list[str] | None = None,
    ) -> None:
        job = self._jobs[job_id]
        job.status = status
        if output_blob_names is not None:
            job.output_blob_names = output_blob_names


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
        except ResourceNotFoundError:
            return None
        return RenderJob.from_dict(json.loads(payload))

    def update(
        self,
        job_id: str,
        *,
        status: RenderStatus,
        output_blob_names: list[str] | None = None,
    ) -> None:
        job = self.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job.status = status
        if output_blob_names is not None:
            job.output_blob_names = output_blob_names
        self._blob(job_id).upload_blob(json.dumps(job.to_dict()), overwrite=True)


class AzureBlobQuotaStore:
    """Atomically consumes fixed-window quotas using Blob ETags."""

    def __init__(self, connection_string: str, container_name: str) -> None:
        from azure.storage.blob import BlobServiceClient

        self._container = BlobServiceClient.from_connection_string(
            connection_string
        ).get_container_client(container_name)

    def consume(self, subject: str, window: str, limit: int) -> bool:
        if limit <= 0:
            return False
        blob = self._container.get_blob_client(f"quotas/{subject}/{window}.json")
        for _ in range(5):
            try:
                download = blob.download_blob()
                payload = json.loads(download.readall())
                count = int(payload["count"])
                if count >= limit:
                    return False
                blob.upload_blob(
                    json.dumps({"count": count + 1}),
                    overwrite=True,
                    etag=download.properties.etag,
                    match_condition=MatchConditions.IfNotModified,
                )
                return True
            except ResourceNotFoundError:
                try:
                    blob.upload_blob(json.dumps({"count": 1}), overwrite=False)
                    return True
                except ResourceExistsError:
                    continue
            except ResourceModifiedError:
                continue
        raise RuntimeError("Could not update the render quota after concurrent writes.")


class BlobDownloader(Protocol):
    def download(self, blob_name: str) -> Iterable[bytes]: ...


class AzureBlobDownloader:
    def __init__(self, connection_string: str, container_name: str) -> None:
        from azure.storage.blob import BlobServiceClient

        self._container = BlobServiceClient.from_connection_string(
            connection_string
        ).get_container_client(container_name)

    def download(self, blob_name: str) -> Iterable[bytes]:
        return self._container.download_blob(blob_name).chunks()


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


def blob_downloader_from_environment() -> BlobDownloader | None:
    if os.getenv("RENDER_JOB_STORE", "memory").lower() != "azure":
        return None
    return AzureBlobDownloader(
        os.environ["AZURE_STORAGE_CONNECTION_STRING"],
        os.environ["RENDER_BLOB_CONTAINER"],
    )


def quota_store_from_environment() -> QuotaStore:
    if os.getenv("RENDER_JOB_STORE", "memory").lower() == "memory":
        return InMemoryQuotaStore()
    return AzureBlobQuotaStore(
        os.environ["AZURE_STORAGE_CONNECTION_STRING"],
        os.environ["RENDER_BLOB_CONTAINER"],
    )
