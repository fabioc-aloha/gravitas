import json
from pathlib import Path

from gravitas_renderer.azure_worker import AzureRenderWorker


class Download:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def readall(self) -> bytes:
        return self._payload


class Blob:
    def __init__(self, name: str, payload: bytes = b"") -> None:
        self.name = name
        self.payload = payload
        self.content_type = None

    def download_blob(self) -> Download:
        return Download(self.payload)

    def upload_blob(self, content, *, overwrite: bool, content_settings=None) -> None:
        self.payload = content.read() if hasattr(content, "read") else content.encode()
        self.content_type = content_settings.content_type if content_settings else None


class Container:
    def __init__(self, job: dict) -> None:
        job_blob_name = f"jobs/{job['job_id']}.json"
        self.blobs = {job_blob_name: Blob(job_blob_name, json.dumps(job).encode())}

    def get_blob_client(self, name: str) -> Blob:
        return self.blobs.setdefault(name, Blob(name))


class Message:
    def __init__(self, content: str) -> None:
        self.content = content


class Queue:
    def __init__(self, job_id: str) -> None:
        self.message = Message(job_id)
        self.deleted = []

    def receive_messages(self, **_kwargs):
        return iter([self.message])

    def delete_message(self, message: Message) -> None:
        self.deleted.append(message)


class Renderer:
    def __init__(self, outputs: list[Path]) -> None:
        self.outputs = outputs
        self.jobs = []

    def render(self, job):
        self.jobs.append(job)
        return self.outputs


def test_worker_persists_private_blob_names_and_metadata_sidecar(tmp_path) -> None:
    job_id = "12345678-1234-5678-1234-567812345678"
    request = {
        "axis_inclination_degrees": 30,
        "background": "deep-space",
        "blue_spectrum": True,
        "disk_thickness": 0.1,
        "disk_temperature": 25_000_000,
        "emissivity_slope": 3,
        "field_of_view": 20,
        "flow_direction": "prograde",
        "inner_disk_radius": 6,
        "jet_strength": 0,
        "magnetic_state": "sane",
        "mass": 1,
        "observing_band": "230-ghz",
        "orbit_degrees": 0,
        "seed": 42,
        "spin": 0.7,
        "zoom": 1,
    }
    job = {"job_id": job_id, "request": request, "status": "queued", "output_blob_names": []}
    names = [
        f"gravitas-{job_id}-5120x1440.png",
        f"gravitas-{job_id}-3440x1440.png",
    ]
    outputs = []
    for name in names:
        output = tmp_path / name
        output.write_bytes(b"png")
        outputs.append(output)
    container = Container(job)
    queue = Queue(job_id)
    renderer = Renderer(outputs)
    worker = AzureRenderWorker.__new__(AzureRenderWorker)
    worker._container = container
    worker._queue = queue
    worker._renderer = renderer

    assert worker.run_once()

    saved = json.loads(container.blobs[f"jobs/{job_id}.json"].payload)
    assert saved["status"] == "complete"
    assert saved["output_blob_names"] == [f"renders/{name}" for name in names]
    assert saved["metadata_blob_name"] == f"renders/gravitas-{job_id}.metadata.json"
    metadata = json.loads(container.blobs[saved["metadata_blob_name"]].payload)
    assert metadata["request"] == request | {"schema_version": 2}
    assert metadata["approximations"] == {
        "orbit_degrees": "screen-space disk azimuth rotation",
        "flow_direction": "Doppler-beaming direction only",
        "blue_spectrum": "artistic disk palette",
        "spin": "Doppler-strength proxy; not Kerr physics",
    }
    assert metadata["provenance_only"] == [
        "background",
        "disk_thickness",
        "jet_strength",
        "magnetic_state",
        "observing_band",
    ]
    assert all(container.blobs[f"renders/{name}"].content_type == "image/png" for name in names)
    assert queue.deleted


def test_worker_acknowledges_non_retryable_malformed_job() -> None:
    job_id = "12345678-1234-5678-1234-567812345678"
    job = {"job_id": job_id, "request": {"mass": "invalid"}, "status": "queued"}
    container = Container(job)
    queue = Queue(job_id)
    worker = AzureRenderWorker.__new__(AzureRenderWorker)
    worker._container = container
    worker._queue = queue
    worker._renderer = Renderer([])

    assert worker.run_once()

    saved = json.loads(container.blobs[f"jobs/{job_id}.json"].payload)
    assert saved["status"] == "failed"
    assert queue.deleted
