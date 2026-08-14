import json
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import RenderRequest
from app.store import InMemoryJobStore, RenderJob, RenderStatus


FULL_REQUEST = {
    "axis_inclination_degrees": 30,
    "background": "deep-space",
    "blue_spectrum": True,
    "disk_thickness": 0.1,
    "disk_temperature": 25_000_000,
    "emissivity_slope": 3,
    "flow_direction": "prograde",
    "inner_disk_radius": 6,
    "jet_strength": 0.4,
    "magnetic_state": "sane",
    "observing_band": "230-ghz",
    "orbit_degrees": 45,
    "seed": 42,
    "spin": 0.7,
    "zoom": 2,
}


def test_post_render_persists_the_complete_request_and_derives_fov() -> None:
    store = InMemoryJobStore()
    response = TestClient(create_app(store)).post("/renders", json=FULL_REQUEST)

    assert response.status_code == 202
    body = response.json()
    UUID(body["job_id"])
    assert body == {"job_id": body["job_id"], "status": "queued"}
    persisted = store.get(body["job_id"]).to_dict()["request"]
    assert persisted == FULL_REQUEST | {"mass": 1.0, "field_of_view": 24.0}


def test_render_request_schema_contains_every_control_with_snake_case_names() -> None:
    schema = RenderRequest.model_json_schema(mode="validation")

    assert set(schema["properties"]) == set(FULL_REQUEST) | {"mass"}
    assert schema["properties"]["mass"]["default"] == 1.0
    assert "field_of_view" not in schema["properties"]


def test_shared_json_schema_field_set_and_required_fields_match_fastapi() -> None:
    shared_schema = json.loads(
        (
            Path(__file__).parents[3]
            / "packages"
            / "render-schema"
            / "render-request.schema.json"
        ).read_text()
    )
    api_schema = RenderRequest.model_json_schema(mode="validation")

    assert set(shared_schema["properties"]) == set(api_schema["properties"])
    assert set(shared_schema["required"]) == set(api_schema["required"])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("axis_inclination_degrees", 86),
        ("disk_thickness", 0.01),
        ("disk_temperature", 999_999),
        ("emissivity_slope", 5.1),
        ("inner_disk_radius", 21),
        ("jet_strength", 1.1),
        ("orbit_degrees", 361),
        ("seed", -1),
        ("spin", 0.999),
        ("zoom", 0.4),
    ],
)
def test_post_render_rejects_values_outside_frontend_bounds(field: str, value: object) -> None:
    response = TestClient(create_app(InMemoryJobStore())).post(
        "/renders", json=FULL_REQUEST | {field: value}
    )

    assert response.status_code == 422


def test_post_render_forbids_a_client_supplied_field_of_view() -> None:
    response = TestClient(create_app(InMemoryJobStore())).post(
        "/renders", json=FULL_REQUEST | {"field_of_view": 999}
    )

    assert response.status_code == 422


class FakeBlobDownloader:
    def __init__(self, content: bytes = b"private png") -> None:
        self.content = content
        self.requested: list[str] = []

    def download(self, blob_name: str):
        self.requested.append(blob_name)
        yield self.content


def completed_job(store: InMemoryJobStore) -> RenderJob:
    job = RenderJob.new(RenderRequest(**FULL_REQUEST))
    store.create(job)
    store.update(
        job.job_id,
        status=RenderStatus.COMPLETE,
        output_blob_names=[
            f"renders/gravitas-{job.job_id}-5120x1440.png",
            f"renders/gravitas-{job.job_id}-3440x1440.png",
        ],
    )
    return job


def test_get_render_returns_api_proxy_download_urls() -> None:
    store = InMemoryJobStore()
    job = completed_job(store)

    response = TestClient(
        create_app(store, public_base_url="https://gravitas.example/api")
    ).get(f"/renders/{job.job_id}")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": job.job_id,
        "status": "complete",
        "output_urls": [
            f"https://gravitas.example/api/renders/{job.job_id}/files/"
            f"gravitas-{job.job_id}-5120x1440.png",
            f"https://gravitas.example/api/renders/{job.job_id}/files/"
            f"gravitas-{job.job_id}-3440x1440.png",
        ],
    }


def test_file_route_streams_a_private_job_blob_as_an_attachment() -> None:
    store = InMemoryJobStore()
    job = completed_job(store)
    downloader = FakeBlobDownloader()
    filename = f"gravitas-{job.job_id}-5120x1440.png"

    response = TestClient(create_app(store, blob_downloader=downloader)).get(
        f"/renders/{job.job_id}/files/{filename}"
    )

    assert response.status_code == 200
    assert response.content == b"private png"
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-disposition"] == f'attachment; filename="{filename}"'
    assert downloader.requested == [f"renders/{filename}"]


def test_file_route_rejects_a_filename_not_owned_by_the_job() -> None:
    store = InMemoryJobStore()
    job = completed_job(store)
    downloader = FakeBlobDownloader()

    response = TestClient(create_app(store, blob_downloader=downloader)).get(
        f"/renders/{job.job_id}/files/another-job.png"
    )

    assert response.status_code == 404
    assert downloader.requested == []


def test_get_render_returns_not_found_for_unknown_job() -> None:
    response = TestClient(create_app(InMemoryJobStore())).get("/renders/not-a-job")

    assert response.status_code == 404


def test_legacy_two_field_job_is_migrated_to_current_defaults() -> None:
    job = RenderJob.from_dict(
        {
            "job_id": "12345678-1234-5678-1234-567812345678",
            "request": {"mass": 1, "field_of_view": 10},
            "status": "queued",
        }
    )

    assert job.request.zoom == 2
    assert job.request.axis_inclination_degrees == 30
    assert job.request.seed == 0
    assert job.to_dict()["schema_version"] == 3


def test_version_two_job_remains_readable_after_field_of_view_recalibration() -> None:
    job = RenderJob.from_dict(
        {
            "schema_version": 2,
            "job_id": "12345678-1234-5678-1234-567812345678",
            "request": FULL_REQUEST | {"mass": 1, "field_of_view": 10},
            "status": "complete",
            "output_blob_names": ["renders/legacy.png"],
        }
    )

    assert job.status == RenderStatus.COMPLETE
    assert job.output_blob_names == ["renders/legacy.png"]
