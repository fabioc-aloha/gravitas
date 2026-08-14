from uuid import UUID

import numpy as np
from PIL import Image

from gravitas_renderer.service import LocalRenderService, RenderJob, render_job_from_request
from gravitas_renderer.schwarzschild import ThinDiskParameters


def test_local_render_service_creates_both_required_uuid_named_pngs(
    tmp_path, monkeypatch
) -> None:
    calls: list[tuple[int, int, float, float, int]] = []

    def fake_shadow_map(
        width: int,
        height: int,
        mass: float,
        field_of_view: float,
        *,
        seed: int,
        disk: object,
        background_image: object,
    ) -> np.ndarray:
        assert disk is None
        assert background_image is None
        calls.append((width, height, mass, field_of_view, seed))
        return np.zeros((height, width, 3), dtype=np.uint8)

    monkeypatch.setattr("gravitas_renderer.service.render_shadow_map", fake_shadow_map)
    job_id = str(UUID("12345678-1234-5678-1234-567812345678"))

    outputs = LocalRenderService(tmp_path).render(
        RenderJob(job_id=job_id, mass=1.0, field_of_view=20.0, seed=73)
    )

    assert calls == [(5120, 1440, 1.0, 20.0, 73), (3440, 1440, 1.0, 20.0, 73)]
    assert [path.name for path in outputs] == [
        f"gravitas-{job_id}-5120x1440.png",
        f"gravitas-{job_id}-3440x1440.png",
    ]
    assert all(path.is_file() for path in outputs)
    assert [Image.open(path).size for path in outputs] == [(5120, 1440), (3440, 1440)]


def test_complete_request_maps_to_render_and_thin_disk_parameters() -> None:
    request = {
        "axis_inclination_degrees": 72,
        "background": "deep-space",
        "blue_spectrum": True,
        "disk_thickness": 0.2,
        "disk_temperature": 50_000_000,
        "emissivity_slope": 2.4,
        "field_of_view": 8.0,
        "flow_direction": "retrograde",
        "inner_disk_radius": 8.0,
        "jet_strength": 0.8,
        "magnetic_state": "mad",
        "mass": 1.5,
        "observing_band": "optical",
        "orbit_degrees": 135,
        "seed": 73,
        "spin": 0.9,
        "zoom": 2.5,
    }

    job = render_job_from_request("12345678-1234-5678-1234-567812345678", request)

    assert job.mass == 1.5
    assert job.field_of_view == 8.0
    assert job.seed == 73
    assert job.disk == ThinDiskParameters(
        inner_radius=8.0,
        outer_radius=16.0,
        temperature_scale=2.0,
        emissivity_slope=0.6,
        inclination_degrees=72,
        doppler_strength=0.69,
        orbit_degrees=135,
        flow_direction="retrograde",
        blue_spectrum=True,
    )
    assert job.provenance == request | {"schema_version": 2}


def test_same_parameters_are_deterministic_and_blue_palette_changes_png_bytes(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("gravitas_renderer.service.OUTPUT_SIZES", ((101, 61), (81, 61)))
    disk = ThinDiskParameters(inner_radius=3, outer_radius=9, blue_spectrum=False)
    blue_disk = ThinDiskParameters(inner_radius=3, outer_radius=9, blue_spectrum=True)
    service = LocalRenderService(tmp_path)

    first = service.render(RenderJob("00000000-0000-0000-0000-000000000001", 1, 20, 9, disk))
    second = service.render(RenderJob("00000000-0000-0000-0000-000000000002", 1, 20, 9, disk))
    changed = service.render(
        RenderJob("00000000-0000-0000-0000-000000000003", 1, 20, 9, blue_disk)
    )

    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
    assert first[0].read_bytes() != changed[0].read_bytes()


def test_legacy_two_field_request_uses_current_render_defaults() -> None:
    job = render_job_from_request(
        "12345678-1234-5678-1234-567812345678",
        {"mass": 1, "field_of_view": 10},
    )

    assert job.field_of_view == 10
    assert job.seed == 0
    assert job.disk is not None
    assert job.disk.inner_radius == 6
    assert job.provenance["schema_version"] == 1
