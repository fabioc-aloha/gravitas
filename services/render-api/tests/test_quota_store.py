import json
from types import SimpleNamespace

from azure.core.exceptions import ResourceExistsError, ResourceModifiedError, ResourceNotFoundError

from app.store import AzureBlobQuotaStore


class Download:
    def __init__(self, count: int, etag: str) -> None:
        self._payload = json.dumps({"count": count}).encode()
        self.properties = SimpleNamespace(etag=etag)

    def readall(self) -> bytes:
        return self._payload


class QuotaBlob:
    def __init__(self, count: int | None = None, *, conflict_once: bool = False) -> None:
        self.count = count
        self.etag = '"0"'
        self.conflict_once = conflict_once

    def download_blob(self) -> Download:
        if self.count is None:
            raise ResourceNotFoundError("missing")
        return Download(self.count, self.etag)

    def upload_blob(self, payload: str, *, overwrite: bool, **_kwargs) -> None:
        if not overwrite and self.count is not None:
            raise ResourceExistsError("exists")
        if overwrite and self.conflict_once:
            self.conflict_once = False
            raise ResourceModifiedError("conflict")
        self.count = int(json.loads(payload)["count"])
        self.etag = f'"{self.count}"'


class Container:
    def __init__(self, blob: QuotaBlob) -> None:
        self.blob = blob
        self.requested_name = None

    def get_blob_client(self, name: str) -> QuotaBlob:
        self.requested_name = name
        return self.blob


def quota_store(blob: QuotaBlob) -> tuple[AzureBlobQuotaStore, Container]:
    container = Container(blob)
    store = AzureBlobQuotaStore.__new__(AzureBlobQuotaStore)
    store._container = container
    return store, container


def test_blob_quota_creates_an_opaque_subject_window_counter() -> None:
    store, container = quota_store(QuotaBlob())

    assert store.consume("hashed-subject", "2026-08-14", 2)
    assert container.requested_name == "quotas/hashed-subject/2026-08-14.json"
    assert container.blob.count == 1


def test_blob_quota_rejects_without_writing_at_the_limit() -> None:
    store, container = quota_store(QuotaBlob(2))

    assert not store.consume("hashed-subject", "2026-08-14", 2)
    assert container.blob.count == 2


def test_blob_quota_retries_an_etag_conflict() -> None:
    store, container = quota_store(QuotaBlob(1, conflict_once=True))

    assert store.consume("hashed-subject", "2026-08-14", 3)
    assert container.blob.count == 2
