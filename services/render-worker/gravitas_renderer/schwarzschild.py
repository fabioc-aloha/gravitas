"""Approximate Schwarzschild reference rasterization.

Capture uses the exact far-field Schwarzschild critical impact parameter.
Escaped-ray bending is deliberately a weak-field screen-space approximation,
not numerical geodesic integration or general-relativistic ray tracing.
"""

from dataclasses import dataclass
from math import sqrt
from typing import Literal

import numpy as np


RayOutcome = Literal["captured", "escaped"]


@dataclass(frozen=True)
class ThinDiskParameters:
    """Controls the direct, projected thin-disk approximation in geometric units."""

    inner_radius: float = 6.0
    outer_radius: float = 12.0
    temperature_scale: float = 1.0
    emissivity_slope: float = 0.75
    inclination_degrees: float = 60.0
    doppler_strength: float = 0.45
    orbit_degrees: float = 0.0
    flow_direction: Literal["prograde", "retrograde"] = "prograde"
    blue_spectrum: bool = False

    def __post_init__(self) -> None:
        if self.inner_radius <= 0 or self.outer_radius <= self.inner_radius:
            raise ValueError("Disk radii must be positive and outer_radius must exceed inner_radius.")
        if self.temperature_scale < 0 or self.emissivity_slope <= 0:
            raise ValueError("Disk temperature scale must be non-negative and slope positive.")
        if not 0 <= self.inclination_degrees < 90:
            raise ValueError("Disk inclination must be in [0, 90) degrees.")
        if self.doppler_strength < 0:
            raise ValueError("Doppler strength must be non-negative.")
        if not 0 <= self.orbit_degrees <= 360:
            raise ValueError("Orbit must be in [0, 360] degrees.")


def critical_impact_parameter(mass: float) -> float:
    """Return the Schwarzschild critical impact parameter in geometric units."""
    if mass <= 0:
        raise ValueError("Mass must be positive.")
    return 3 * sqrt(3) * mass


def classify_impact_parameter(impact_parameter: float, mass: float) -> RayOutcome:
    """Classify a far-field null ray using the Schwarzschild capture threshold."""
    if impact_parameter < 0:
        raise ValueError("Impact parameter must not be negative.")
    return "captured" if impact_parameter <= critical_impact_parameter(mass) else "escaped"


def thin_disk_intensity(
    radius: float | np.ndarray,
    azimuth: float | np.ndarray,
    parameters: ThinDiskParameters,
) -> float | np.ndarray:
    """Return a dimensionless Novikov-Thorne-inspired radial disk brightness.

    The zero-torque inner-edge factor and T^4 emissivity are retained, while
    transfer, redshift, and lensing are intentionally not solved here.
    """
    radius_array = np.asarray(radius, dtype=np.float32)
    azimuth_array = np.asarray(azimuth, dtype=np.float32)
    inside = (radius_array >= parameters.inner_radius) & (
        radius_array <= parameters.outer_radius
    )
    safe_radius = np.maximum(radius_array, parameters.inner_radius)
    edge_factor = np.clip(
        1 - np.sqrt(parameters.inner_radius / safe_radius), 0, None
    ) ** 0.25
    temperature = (
        parameters.temperature_scale
        * (safe_radius / parameters.inner_radius) ** (-parameters.emissivity_slope)
        * edge_factor
    )
    inclination = np.deg2rad(parameters.inclination_degrees)
    beaming_azimuth = azimuth_array - np.deg2rad(parameters.orbit_degrees)
    flow_sign = 1 if parameters.flow_direction == "prograde" else -1
    doppler = np.maximum(
        0.0,
        1
        + flow_sign
        * parameters.doppler_strength
        * np.sin(inclination)
        * np.sin(beaming_azimuth),
    ) ** 3
    intensity = np.where(inside, temperature**4 * doppler, 0.0)
    return float(intensity) if intensity.ndim == 0 else intensity


def _deflected_celestial_sphere(
    impact: np.ndarray, azimuth: np.ndarray, mass: float, seed: int
) -> np.ndarray:
    """Sample a deterministic procedural sky after weak-field radial bending."""
    critical = critical_impact_parameter(mass)
    # alpha = 4M/b is the leading Schwarzschild weak-field deflection term.
    # It is capped near the photon sphere because this renderer does not
    # integrate strong-field geodesics or construct multiple images.
    deflection = np.minimum(4 * mass / np.maximum(impact, critical * 1.05), 1.25)
    source_polar = np.arctan(impact / 10.0) + deflection
    longitude = azimuth / (2 * np.pi) + 0.5
    latitude = source_polar / np.pi

    band = np.exp(-((latitude - 0.52 - 0.08 * np.sin(longitude * 5)) / 0.09) ** 2)
    wave = 0.5 + 0.5 * np.sin(longitude * 33 + latitude * 19 + seed * 0.17)
    cell_x = np.floor(longitude * 1300)
    cell_y = np.floor(latitude * 700)
    hashed = np.sin(cell_x * 12.9898 + cell_y * 78.233 + seed * 37.719) * 43758.5453
    hashed -= np.floor(hashed)
    stars = np.clip((hashed - 0.994) * 140, 0, 1)

    sky = np.empty((*impact.shape, 3), dtype=np.float32)
    sky[..., 0] = 3 + 8 * band + 3 * wave + 230 * stars
    sky[..., 1] = 8 + 17 * band + 7 * wave + 230 * stars
    sky[..., 2] = 20 + 40 * band + 15 * wave + 230 * stars
    return sky


def _deflected_background_texture(
    background_image: np.ndarray,
    screen_x: np.ndarray,
    screen_y: np.ndarray,
    impact: np.ndarray,
    mass: float,
    horizontal_field: float,
    vertical_field: float,
) -> np.ndarray:
    """Sample an aspect-cropped RGB texture through weak radial deflection."""
    if background_image.ndim != 3 or background_image.shape[2] != 3:
        raise ValueError("Background image must have RGB channels.")

    critical = critical_impact_parameter(mass)
    deflection = np.minimum(4 * mass / np.maximum(impact, critical * 1.05), 1.25)
    radial_scale = (impact + deflection) / np.maximum(
        impact, np.finfo(np.float32).eps
    )
    u = np.clip(screen_x * radial_scale / horizontal_field + 0.5, 0, 1)
    v = np.clip(screen_y * radial_scale / vertical_field + 0.5, 0, 1)

    source_height, source_width = background_image.shape[:2]
    target_aspect = horizontal_field / vertical_field
    source_aspect = source_width / source_height
    if source_aspect > target_aspect:
        crop_height = source_height
        crop_width = round(crop_height * target_aspect)
        crop_x = (source_width - crop_width) // 2
        crop_y = 0
    else:
        crop_width = source_width
        crop_height = round(crop_width / target_aspect)
        crop_x = 0
        crop_y = (source_height - crop_height) // 2

    sample_x = np.clip(
        crop_x + np.rint(u * (crop_width - 1)), 0, source_width - 1
    ).astype(int)
    sample_y = np.clip(
        crop_y + np.rint(v * (crop_height - 1)), 0, source_height - 1
    ).astype(int)
    return background_image[sample_y, sample_x].astype(np.float32)


def _thin_disk_layer(
    screen_x: np.ndarray, screen_y: np.ndarray, parameters: ThinDiskParameters
) -> np.ndarray:
    inclination = np.deg2rad(parameters.inclination_degrees)
    orbit = np.deg2rad(parameters.orbit_degrees)
    disk_x = np.cos(orbit) * screen_x + np.sin(orbit) * screen_y
    projected_y = -np.sin(orbit) * screen_x + np.cos(orbit) * screen_y
    disk_y = projected_y / max(np.cos(inclination), 0.01)
    radius = np.hypot(disk_x, disk_y)
    azimuth = np.arctan2(disk_y, disk_x)
    intensity = thin_disk_intensity(radius, azimuth, parameters)
    exposure = 1 - np.exp(-intensity * 80)
    layer = np.empty((*radius.shape, 3), dtype=np.float32)
    if parameters.blue_spectrum:
        layer[..., 0] = 95 * exposure
        layer[..., 1] = 190 * exposure
        layer[..., 2] = 255 * exposure
    else:
        layer[..., 0] = 255 * exposure
        layer[..., 1] = 175 * exposure
        layer[..., 2] = 85 * exposure
    return layer


def render_shadow_map(
    width: int,
    height: int,
    mass: float,
    field_of_view: float,
    *,
    seed: int = 0,
    disk: ThinDiskParameters | None = None,
    background_image: np.ndarray | None = None,
) -> np.ndarray:
    """Rasterize capture, an approximate deflected sky, and a direct thin disk.

    This is a deterministic artistic reference raster. Only the capture
    threshold is exact Schwarzschild physics; escaped rays use the leading
    weak-field ``4M/b`` bend with a strong-field cap. It is not a full GRRT
    implementation and does not model geodesic disk intersections.
    """
    if width <= 0 or height <= 0:
        raise ValueError("Raster dimensions must be positive.")
    if field_of_view <= 0:
        raise ValueError("Field of view must be positive.")
    if not isinstance(seed, int):
        raise ValueError("Seed must be an integer.")

    parameters = disk or ThinDiskParameters()
    aspect_ratio = width / height
    horizontal_field = field_of_view * aspect_ratio
    x = np.linspace(-horizontal_field / 2, horizontal_field / 2, width, dtype=np.float32)
    y = np.linspace(-field_of_view / 2, field_of_view / 2, height, dtype=np.float32)
    screen_x, screen_y = np.broadcast_arrays(x[None, :], y[:, None])
    impact = np.hypot(screen_x, screen_y)
    captured = impact <= critical_impact_parameter(mass)

    sky = (
        _deflected_background_texture(
            background_image,
            screen_x,
            screen_y,
            impact,
            mass,
            horizontal_field,
            field_of_view,
        )
        if background_image is not None
        else _deflected_celestial_sphere(
            impact, np.arctan2(screen_y, screen_x), mass, seed
        )
    )
    sky += _thin_disk_layer(screen_x, screen_y, parameters)
    sky[captured] = 0
    return np.clip(sky, 0, 255).astype(np.uint8)
