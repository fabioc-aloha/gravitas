from gravitas_renderer.schwarzschild import (
    classify_impact_parameter,
    critical_impact_parameter,
    render_shadow_map,
)


def test_critical_impact_parameter_matches_schwarzschild_shadow() -> None:
    assert critical_impact_parameter(1.0) == 3 * 3**0.5


def test_rays_inside_critical_impact_parameter_are_captured() -> None:
    assert classify_impact_parameter(5.0, mass=1.0) == "captured"
    assert classify_impact_parameter(5.3, mass=1.0) == "escaped"


def test_shadow_map_captures_center_rays_and_preserves_distant_sky() -> None:
    image = render_shadow_map(width=9, height=9, mass=1.0, field_of_view=20.0)

    assert image.shape == (9, 9, 3)
    assert image[4, 4].tolist() == [0, 0, 0]
    assert image[0, 0].max() > 0
