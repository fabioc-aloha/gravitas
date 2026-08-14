from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .models import RenderRequest
from .store import InMemoryJobStore, JobStore, RenderJob, job_store_from_environment


def create_app(store: JobStore | None = None) -> FastAPI:
    app = FastAPI(title="Gravitas Render API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    if store is None:
        store = job_store_from_environment()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"service": "gravitas-render-api", "status": "ok"}

    @app.post("/renders", status_code=status.HTTP_202_ACCEPTED)
    def create_render(request: RenderRequest) -> dict[str, str]:
        job = RenderJob.new(request.mass, request.field_of_view)
        store.create(job)
        return {"job_id": job.job_id, "status": job.status}

    @app.get("/renders/{job_id}")
    def get_render(job_id: str) -> dict[str, object]:
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found.")
        response: dict[str, object] = {"job_id": job.job_id, "status": job.status}
        if job.status == "complete":
            response["output_urls"] = job.output_urls
        return response

    return app


app = create_app()
