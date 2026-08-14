#!/usr/bin/env python3
"""Exercise the deployed Gravitas stack through its public HTTP boundary."""

from __future__ import annotations

import argparse
import json
import struct
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


EXPECTED_OUTPUTS = {(5120, 1440), (3440, 1440)}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RENDER_REQUEST = {
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
    "mass": 1,
    "observing_band": "230-ghz",
    "orbit_degrees": 0,
    "seed": 42,
    "spin": 0,
    "zoom": 0.7,
}


def request_bytes(
    url: str, *, data: bytes | None = None, token: str | None = None
) -> tuple[bytes, str]:
    headers = {"Content-Type": "application/json"} if data is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, data=data, headers=headers)
    with urlopen(request, timeout=60) as response:
        return response.read(), response.headers.get_content_type()


def request_json(
    url: str, *, payload: dict[str, object] | None = None, token: str | None = None
) -> dict[str, object]:
    data = json.dumps(payload).encode() if payload is not None else None
    body, content_type = request_bytes(url, data=data, token=token)
    if content_type != "application/json":
        raise AssertionError(f"Expected JSON from {url}, received {content_type}.")
    return json.loads(body)


def png_dimensions(url: str, token: str) -> tuple[int, int]:
    request = Request(url, headers={"Authorization": f"Bearer {token}"})
    with urlopen(request, timeout=120) as response:
        header = response.read(24)
        if response.headers.get_content_type() != "image/png":
            raise AssertionError(f"Expected PNG from {url}.")
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise AssertionError(f"Invalid PNG header from {url}.")
    return struct.unpack(">II", header[16:24])


def wait_for_render(
    api_url: str, job_id: str, token: str, timeout_seconds: int
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    status_url = urljoin(f"{api_url}/", f"ci/renders/{job_id}")
    last_status = "queued"
    while time.monotonic() < deadline:
        job = request_json(status_url, token=token)
        last_status = str(job.get("status"))
        print(f"Render {job_id}: {last_status}", flush=True)
        if last_status == "complete":
            return job
        if last_status == "failed":
            raise AssertionError(f"Render {job_id} failed.")
        time.sleep(5)
    raise TimeoutError(
        f"Render {job_id} remained {last_status} after {timeout_seconds} seconds."
    )


def expect_rejected(url: str, *, payload: dict[str, object] | None = None) -> None:
    try:
        request_json(url, payload=payload)
    except HTTPError as error:
        if error.code in (401, 403, 404):
            return
        raise
    raise AssertionError(f"Expected unauthenticated request to be rejected: {url}")


def run(
    web_url: str,
    api_url: str,
    direct_api_url: str,
    service_token: str,
    timeout_seconds: int,
) -> None:
    web_body, web_content_type = request_bytes(web_url)
    if web_content_type != "text/html" or b"Gravitas" not in web_body:
        raise AssertionError("The deployed web app did not return the Gravitas HTML shell.")

    health = request_json(urljoin(f"{api_url}/", "health"))
    if health != {"service": "gravitas-render-api", "status": "ok"}:
        raise AssertionError(f"Unexpected API health response: {health}")

    expect_rejected(urljoin(f"{direct_api_url}/", "api/health"))
    expect_rejected(urljoin(f"{api_url}/", "renders"), payload=RENDER_REQUEST)

    created = request_json(
        urljoin(f"{api_url}/", "ci/renders"),
        payload=RENDER_REQUEST,
        token=service_token,
    )
    job_id = str(created.get("job_id", ""))
    if not job_id or created.get("status") != "queued":
        raise AssertionError(f"Unexpected render submission response: {created}")

    completed = wait_for_render(api_url, job_id, service_token, timeout_seconds)
    output_urls = completed.get("output_urls")
    if not isinstance(output_urls, list) or len(output_urls) != 2:
        raise AssertionError(f"Render {job_id} did not return two output URLs.")
    dimensions = {png_dimensions(str(url), service_token) for url in output_urls}
    if dimensions != EXPECTED_OUTPUTS:
        raise AssertionError(f"Unexpected output dimensions: {sorted(dimensions)}")
    print(f"Live Gravitas render {job_id} passed with outputs {sorted(dimensions)}.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-url", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--direct-api-url", required=True)
    parser.add_argument("--service-token", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    try:
        run(
            args.web_url.rstrip("/"),
            args.api_url.rstrip("/"),
            args.direct_api_url.rstrip("/"),
            args.service_token,
            args.timeout_seconds,
        )
    except (AssertionError, HTTPError, TimeoutError, URLError, ValueError) as error:
        print(f"LIVE TEST FAILED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
