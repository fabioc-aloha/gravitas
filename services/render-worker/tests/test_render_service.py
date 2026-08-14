from uuid import UUID

import numpy as np

from gravitas_renderer.service import LocalRenderService, RenderJob


def test_local_render_service_creates_both_required_uuid_named_pngs(
    tmp_path, monkeypatch
) -> None:
    calls: list[tuple[int, int, float, float]] = []

    def fake_shadow_map(width: int, height: int, mass: float, field_of_view: float) -> np.ndarray:
        calls.append((width, height, mass, field_of_view))
        return np.zeros((2, 2, 3), dtype=np.uint8)

    monkeypatch.setattr("gravitas_renderer.service.render_shadow_map", fake_shadow_map)
    job_id = str(UUID("12345678-1234-5678-1234-567812345678"))

    outputs = LocalRenderService(tmp_path).render(
        RenderJob(job_id=job_id, mass=1.0, field_of_view=20.0)
    )

    assert calls == [(5120, 1440, 1.0, 20.0), (3440, 1440, 1.0, 20.0)]
    assert [path.name for path in outputs] == [
        f"gravitas-{job_id}-5120x1440.png",
        f"gravitas-{job_id}-3440x1440.png",
    ]
    assert all(path.is_file() for path in outputs)
