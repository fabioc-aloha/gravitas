from math import sqrt
from typing import Literal

import numpy as np


RayOutcome = Literal["captured", "escaped"]


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


def render_shadow_map(width: int, height: int, mass: float, field_of_view: float) -> np.ndarray:
    """Rasterize far-field ray capture against a Schwarzschild shadow.

    This first reference pass models capture exactly at the Schwarzschild
    critical impact parameter. It does not yet integrate escaped geodesics
    into a lensed background or accretion disk.
    """
    if width <= 0 or height <= 0:
        raise ValueError("Raster dimensions must be positive.")
    if field_of_view <= 0:
        raise ValueError("Field of view must be positive.")

    x = np.linspace(-field_of_view / 2, field_of_view / 2, width)
    y = np.linspace(-field_of_view / 2, field_of_view / 2, height)
    screen_x, screen_y = np.meshgrid(x, y)
    impact = np.hypot(screen_x, screen_y)
    captured = impact <= critical_impact_parameter(mass)

    radius = np.clip(impact / (field_of_view * 0.71), 0, 1)
    sky = np.empty((height, width, 3), dtype=np.uint8)
    sky[..., 0] = (8 + 16 * (1 - radius)).astype(np.uint8)
    sky[..., 1] = (19 + 34 * (1 - radius)).astype(np.uint8)
    sky[..., 2] = (43 + 64 * (1 - radius)).astype(np.uint8)
    sky[captured] = 0
    return sky
