from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .schwarzschild import render_shadow_map

OUTPUT_SIZES = ((5120, 1440), (3440, 1440))


@dataclass(frozen=True)
class RenderJob:
    job_id: str
    mass: float
    field_of_view: float


class LocalRenderService:
    """Renders PNG artifacts locally; cloud workers can upload its results."""

    def __init__(self, output_directory: Path) -> None:
        self._output_directory = output_directory

    def render(self, job: RenderJob) -> list[Path]:
        self._output_directory.mkdir(parents=True, exist_ok=True)
        outputs = []
        for width, height in OUTPUT_SIZES:
            image = render_shadow_map(width, height, job.mass, job.field_of_view)
            output = self._output_directory / f"gravitas-{job.job_id}-{width}x{height}.png"
            Image.fromarray(image).save(output, format="PNG")
            outputs.append(output)
        return outputs
