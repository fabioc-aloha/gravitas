import numpy as np

from gravitas_renderer.schwarzschild import (
    ThinDiskParameters,
    classify_impact_parameter,
    critical_impact_parameter,
    render_shadow_map,
    thin_disk_intensity,
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


def test_ultrawide_raster_preserves_a_circular_schwarzschild_shadow() -> None:
    image = render_shadow_map(width=320, height=90, mass=1.0, field_of_view=20.0)
    captured_y, captured_x = np.where(np.all(image == 0, axis=2))

    shadow_width = captured_x.max() - captured_x.min() + 1
    shadow_height = captured_y.max() - captured_y.min() + 1

    assert abs(shadow_width - shadow_height) <= 2


def test_escaped_rays_sample_a_seeded_deflected_celestial_sphere() -> None:
    no_lens = render_shadow_map(
        width=81, height=81, mass=0.01, field_of_view=20.0, seed=17
    )
    lensed = render_shadow_map(
        width=81, height=81, mass=1.0, field_of_view=20.0, seed=17
    )

    assert no_lens[0, 0].max() > 0
    assert np.any(no_lens[0, 20] != lensed[0, 20])


def test_escaped_rays_can_sample_a_real_background_texture() -> None:
    background = np.full((24, 48, 3), [120, 40, 20], dtype=np.uint8)
    disk = ThinDiskParameters(temperature_scale=0)

    image = render_shadow_map(
        width=81,
        height=41,
        mass=0.01,
        field_of_view=20,
        background_image=background,
        disk=disk,
    )

    assert image[0, 0].tolist() == [120, 40, 20]


def test_thin_disk_profile_and_doppler_asymmetry_are_configurable() -> None:
    symmetric = ThinDiskParameters(
        inner_radius=6.0,
        outer_radius=12.0,
        temperature_scale=1.0,
        emissivity_slope=0.75,
        inclination_degrees=60.0,
        doppler_strength=0.0,
    )
    asymmetric = ThinDiskParameters(
        inner_radius=6.0,
        outer_radius=12.0,
        temperature_scale=2.0,
        emissivity_slope=0.75,
        inclination_degrees=60.0,
        doppler_strength=0.6,
    )

    assert thin_disk_intensity(5.9, 0.0, symmetric) == 0.0
    assert thin_disk_intensity(12.0, 0.0, symmetric) == 0.0
    assert thin_disk_intensity(7.0, 0.0, asymmetric) > thin_disk_intensity(
        7.0, 0.0, symmetric
    )
    assert thin_disk_intensity(7.0, np.pi / 2, asymmetric) > thin_disk_intensity(
        7.0, -np.pi / 2, asymmetric
    )


def test_seeded_rendering_is_byte_deterministic() -> None:
    kwargs = dict(width=101, height=61, mass=1.0, field_of_view=20.0, seed=99)

    first = render_shadow_map(**kwargs)
    second = render_shadow_map(**kwargs)
    changed_seed = render_shadow_map(**(kwargs | {"seed": 100}))

    assert np.array_equal(first, second)
    assert not np.array_equal(first, changed_seed)


def test_orbit_retrograde_flow_and_blue_palette_change_the_approximation() -> None:
    base = ThinDiskParameters(
        inner_radius=3,
        outer_radius=9,
        inclination_degrees=60,
        doppler_strength=0.6,
    )
    orbit = ThinDiskParameters(
        inner_radius=3,
        outer_radius=9,
        inclination_degrees=60,
        doppler_strength=0.6,
        orbit_degrees=90,
    )
    retrograde = ThinDiskParameters(
        inner_radius=3,
        outer_radius=9,
        inclination_degrees=60,
        doppler_strength=0.6,
        flow_direction="retrograde",
    )
    blue = ThinDiskParameters(
        inner_radius=3,
        outer_radius=9,
        inclination_degrees=60,
        doppler_strength=0.6,
        blue_spectrum=True,
    )

    images = [
        render_shadow_map(101, 61, 1, 20, seed=42, disk=parameters)
        for parameters in (base, orbit, retrograde, blue)
    ]

    assert all(not np.array_equal(images[0], changed) for changed in images[1:])
