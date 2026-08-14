import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .schwarzschild import ThinDiskParameters, render_shadow_map

OUTPUT_SIZES = ((5120, 1440), (3440, 1440))
LEGACY_REQUEST_DEFAULTS: dict[str, object] = {
    "axis_inclination_degrees": 30,
    "background": "deep-space",
    "blue_spectrum": True,
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
    "spin": 0.7,
    "zoom": 1,
}


@dataclass(frozen=True)
class RenderJob:
    job_id: str
    mass: float
    field_of_view: float
    seed: int = 0
    disk: ThinDiskParameters | None = None
    provenance: dict[str, object] = field(default_factory=dict)


def render_job_from_request(job_id: str, request: dict[str, object]) -> RenderJob:
    normalized = dict(request)
    is_legacy = "axis_inclination_degrees" not in normalized
    if is_legacy:
        normalized = LEGACY_REQUEST_DEFAULTS | normalized
    field_of_view = float(normalized["field_of_view"])
    inner_radius = float(normalized["inner_disk_radius"])
    spin = float(normalized["spin"])
    disk = ThinDiskParameters(
        inner_radius=inner_radius,
        outer_radius=max(inner_radius * 2, inner_radius + 6),
        temperature_scale=float(normalized["disk_temperature"]) / 25_000_000,
        emissivity_slope=float(normalized["emissivity_slope"]),
        inclination_degrees=float(normalized["axis_inclination_degrees"]),
        doppler_strength=round(0.15 + 0.6 * spin, 12),
        orbit_degrees=float(normalized["orbit_degrees"]),
        flow_direction=str(normalized["flow_direction"]),
        blue_spectrum=bool(normalized["blue_spectrum"]),
    )
    return RenderJob(
        job_id=job_id,
        mass=float(normalized["mass"]),
        field_of_view=field_of_view,
        seed=int(normalized["seed"]),
        disk=disk,
        provenance=normalized | {"schema_version": 1 if is_legacy else 2},
    )


class LocalRenderService:
    """Renders PNG artifacts locally; cloud workers can upload its results."""

    def __init__(self, output_directory: Path, background_path: Path | None = None) -> None:
        self._output_directory = output_directory
        configured_background = background_path or (
            Path(value) if (value := os.getenv("RENDER_BACKGROUND_PATH")) else None
        )
        self._background_image = (
            np.asarray(Image.open(configured_background).convert("RGB"))
            if configured_background and configured_background.is_file()
            else None
        )

    def render(self, job: RenderJob) -> list[Path]:
        self._output_directory.mkdir(parents=True, exist_ok=True)
        outputs = []
        for width, height in OUTPUT_SIZES:
            image = render_shadow_map(
                width,
                height,
                job.mass,
                job.field_of_view,
                seed=job.seed,
                disk=job.disk,
                background_image=(
                    self._background_image
                    if job.provenance.get("background") == "deep-space"
                    else None
                ),
            )
            output = self._output_directory / f"gravitas-{job.job_id}-{width}x{height}.png"
            Image.fromarray(image).save(output, format="PNG")
            outputs.append(output)
        return outputs
