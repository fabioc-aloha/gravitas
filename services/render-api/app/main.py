import os
from pathlib import PurePosixPath
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import RenderRequest
from .store import (
    BlobDownloader,
    JobStore,
    RenderJob,
    RenderStatus,
    blob_downloader_from_environment,
    job_store_from_environment,
)


def create_app(
    store: JobStore | None = None,
    *,
    blob_downloader: BlobDownloader | None = None,
    public_base_url: str | None = None,
) -> FastAPI:
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
        blob_downloader = blob_downloader or blob_downloader_from_environment()
    configured_public_base_url = public_base_url or os.getenv("RENDER_PUBLIC_BASE_URL")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"service": "gravitas-render-api", "status": "ok"}

    @app.post("/renders", status_code=status.HTTP_202_ACCEPTED)
    def create_render(request: RenderRequest) -> dict[str, str]:
        job = RenderJob.new(request)
        store.create(job)
        return {"job_id": job.job_id, "status": job.status}

    @app.get("/renders/{job_id}")
    def get_render(job_id: str, request: Request) -> dict[str, object]:
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found.")
        response: dict[str, object] = {"job_id": job.job_id, "status": job.status}
        if job.status == "complete":
            base_url = (configured_public_base_url or str(request.base_url)).rstrip("/")
            response["output_urls"] = [
                f"{base_url}/renders/{quote(job.job_id, safe='')}/files/"
                f"{quote(PurePosixPath(blob_name).name, safe='')}"
                for blob_name in job.output_blob_names
            ]
        return response

    @app.get("/renders/{job_id}/files/{filename}")
    def download_render(job_id: str, filename: str) -> StreamingResponse:
        job = store.get(job_id)
        if job is None or job.status != RenderStatus.COMPLETE:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render not found.")
        matching_blob = next(
            (
                blob_name
                for blob_name in job.output_blob_names
                if PurePosixPath(blob_name).name == filename
            ),
            None,
        )
        if matching_blob is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render file not found.")
        if blob_downloader is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Render download storage is unavailable.",
            )
        return StreamingResponse(
            blob_downloader.download(matching_blob),
            media_type="image/png",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return app


app = create_app()
