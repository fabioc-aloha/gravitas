# Schwarzschild Raster Baseline

The first Gravitas reference rasterizer models far-field null-ray capture around a non-spinning Schwarzschild black hole.

## Implemented

- Critical impact parameter: `b_crit = 3 sqrt(3) M`.
- Vectorized screen-plane impact-parameter calculation.
- Capture classification: rays with `b <= b_crit` enter the shadow; remaining rays sample a placeholder sky.

## Not yet implemented

- Escaped-geodesic integration and background deflection.
- Thin-disk intersections and higher-order lensed disk images.
- Kerr spin, frame dragging, ISCO-derived disk edges, and relativistic transfer.

This is a correctness baseline for the shadow boundary, not yet a full general-relativistic transfer renderer.
