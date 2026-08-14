from uuid import UUID

from fastapi.testclient import TestClient

from app.main import create_app
from app.store import InMemoryJobStore, RenderJob, RenderStatus


def test_post_render_queues_a_uuid_backed_job() -> None:
    store = InMemoryJobStore()
    response = TestClient(create_app(store)).post(
        "/renders", json={"mass": 1.0, "field_of_view": 20.0}
    )

    assert response.status_code == 202
    body = response.json()
    UUID(body["job_id"])
    assert body == {"job_id": body["job_id"], "status": "queued"}
    assert store.get(body["job_id"]).request.mass == 1.0


def test_post_render_rejects_an_invalid_minimal_request() -> None:
    response = TestClient(create_app(InMemoryJobStore())).post(
        "/renders", json={"mass": 0, "field_of_view": 20.0}
    )

    assert response.status_code == 422


def test_get_render_returns_complete_output_urls() -> None:
    store = InMemoryJobStore()
    job = RenderJob.new(mass=1.0, field_of_view=20.0)
    store.create(job)
    store.update(
        job.job_id,
        status=RenderStatus.COMPLETE,
        output_urls=[
            "https://downloads.example/gravitas-a-5120x1440.png",
            "https://downloads.example/gravitas-a-3440x1440.png",
        ],
    )

    response = TestClient(create_app(store)).get(f"/renders/{job.job_id}")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": job.job_id,
        "status": "complete",
        "output_urls": [
            "https://downloads.example/gravitas-a-5120x1440.png",
            "https://downloads.example/gravitas-a-3440x1440.png",
        ],
    }


def test_get_render_returns_not_found_for_unknown_job() -> None:
    response = TestClient(create_app(InMemoryJobStore())).get("/renders/not-a-job")

    assert response.status_code == 404
