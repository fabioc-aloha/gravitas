import base64
import binascii
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from pathlib import PurePosixPath
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import RenderRequest
from .store import (
    BlobDownloader,
    InMemoryQuotaStore,
    JobStore,
    QuotaStore,
    RenderJob,
    RenderStatus,
    blob_downloader_from_environment,
    job_store_from_environment,
    quota_store_from_environment,
)


def _positive_int(value: int | str, name: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{name} must be positive.")
    return parsed


def _principal_subject(header: str | None) -> str | None:
    if not header or len(header) > 16_384:
        return None
    try:
        payload = json.loads(base64.b64decode(header, validate=True))
    except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return None
    provider = payload.get("identityProvider")
    user_id = payload.get("userId")
    roles = payload.get("userRoles")
    if (
        not isinstance(provider, str)
        or not provider
        or not isinstance(user_id, str)
        or not user_id
        or not isinstance(roles, list)
        or "authenticated" not in roles
    ):
        return None
    return hashlib.sha256(f"{provider}:{user_id}".encode()).hexdigest()


def _require_principal(request: Request) -> str:
    subject = _principal_subject(request.headers.get("x-ms-client-principal"))
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in is required to render wallpapers.",
        )
    return subject


def _require_service(request: Request, expected_token: str) -> str:
    authorization = request.headers.get("authorization", "")
    scheme, _, supplied_token = authorization.partition(" ")
    if (
        not expected_token
        or scheme.lower() != "bearer"
        or not supplied_token
        or not hmac.compare_digest(supplied_token, expected_token)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")
    return "service:ci"


def create_app(
    store: JobStore | None = None,
    *,
    blob_downloader: BlobDownloader | None = None,
    public_base_url: str | None = None,
    quota_store: QuotaStore | None = None,
    daily_quota: int | None = None,
    smoke_token: str | None = None,
    smoke_daily_quota: int | None = None,
    allowed_origins: list[str] | None = None,
) -> FastAPI:
    app = FastAPI(title="Gravitas Render API")
    configured_origins = allowed_origins
    if configured_origins is None:
        configured_origins = [
            origin.strip()
            for origin in os.getenv("RENDER_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
            if origin.strip()
        ]
    if configured_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=configured_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )

    if store is None:
        store = job_store_from_environment()
        blob_downloader = blob_downloader or blob_downloader_from_environment()
        quota_store = quota_store or quota_store_from_environment()
    else:
        quota_store = quota_store or InMemoryQuotaStore()
    configured_public_base_url = public_base_url or os.getenv("RENDER_PUBLIC_BASE_URL")
    configured_daily_quota = _positive_int(
        daily_quota or os.getenv("RENDER_DAILY_QUOTA", "10"), "RENDER_DAILY_QUOTA"
    )
    configured_smoke_quota = _positive_int(
        smoke_daily_quota or os.getenv("RENDER_SMOKE_DAILY_QUOTA", "50"),
        "RENDER_SMOKE_DAILY_QUOTA",
    )
    configured_smoke_token = smoke_token if smoke_token is not None else os.getenv(
        "RENDER_SMOKE_TOKEN", ""
    )

    def consume_quota(subject: str, limit: int) -> None:
        window = datetime.now(UTC).date().isoformat()
        if not quota_store.consume(subject, window, limit):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily render quota exceeded.",
                headers={"Retry-After": "86400"},
            )

    def create_owned_render(render_request: RenderRequest, owner_id: str) -> dict[str, str]:
        job = RenderJob.new(render_request, owner_id=owner_id)
        store.create(job)
        return {"job_id": job.job_id, "status": job.status}

    def owned_job(job_id: str, owner_id: str) -> RenderJob:
        job = store.get(job_id)
        if job is None or job.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found."
            )
        return job

    def render_response(
        job: RenderJob, request: Request, route_prefix: str
    ) -> dict[str, object]:
        response: dict[str, object] = {"job_id": job.job_id, "status": job.status}
        if job.status == RenderStatus.COMPLETE:
            base_url = (configured_public_base_url or str(request.base_url)).rstrip("/")
            response["output_urls"] = [
                f"{base_url}/{route_prefix}/{quote(job.job_id, safe='')}/files/"
                f"{quote(PurePosixPath(blob_name).name, safe='')}"
                for blob_name in job.output_blob_names
            ]
        return response

    def download_owned_render(
        job_id: str, filename: str, owner_id: str
    ) -> StreamingResponse:
        job = owned_job(job_id, owner_id)
        if job.status != RenderStatus.COMPLETE:
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Render file not found."
            )
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

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"service": "gravitas-render-api", "status": "ok"}

    @app.post("/api/renders", status_code=status.HTTP_202_ACCEPTED)
    def create_render(render_request: RenderRequest, request: Request) -> dict[str, str]:
        owner_id = _require_principal(request)
        consume_quota(owner_id, configured_daily_quota)
        return create_owned_render(render_request, owner_id)

    @app.get("/api/renders/{job_id}")
    def get_render(job_id: str, request: Request) -> dict[str, object]:
        job = owned_job(job_id, _require_principal(request))
        return render_response(job, request, "renders")

    @app.get("/api/renders/{job_id}/files/{filename}")
    def download_render(
        job_id: str, filename: str, request: Request
    ) -> StreamingResponse:
        return download_owned_render(job_id, filename, _require_principal(request))

    @app.post("/api/ci/renders", status_code=status.HTTP_202_ACCEPTED)
    def create_ci_render(render_request: RenderRequest, request: Request) -> dict[str, str]:
        owner_id = _require_service(request, configured_smoke_token)
        consume_quota(owner_id, configured_smoke_quota)
        return create_owned_render(render_request, owner_id)

    @app.get("/api/ci/renders/{job_id}")
    def get_ci_render(job_id: str, request: Request) -> dict[str, object]:
        owner_id = _require_service(request, configured_smoke_token)
        return render_response(owned_job(job_id, owner_id), request, "ci/renders")

    @app.get("/api/ci/renders/{job_id}/files/{filename}")
    def download_ci_render(
        job_id: str, filename: str, request: Request
    ) -> StreamingResponse:
        owner_id = _require_service(request, configured_smoke_token)
        return download_owned_render(job_id, filename, owner_id)

    return app


app = create_app()
