# Gravitas

![Gravitas banner](assets/gravitas-banner.svg)

**Generative black-hole scenes, grounded in relativity.**

Gravitas generates scientifically informed black-hole wallpapers for Douglas. It separates interactive visual exploration from research-grounded final rendering, preserving the difference between physical simulation and intentional artistic direction.

## Output formats

Every completed render exports both target monitor sizes:

| Format | Resolution | Aspect ratio |
|---|---:|---:|
| Super ultrawide | 5120×1440 | 32:9 |
| Ultrawide | 3440×1440 | 43:18 |

## Product architecture

```text
Web app (React + WebGPU preview)
        |
        v
Azure API / job queue
        |
        v
CPU render worker -> Blob Storage -> dual-size PNG + metadata
        |
        +-> Optional GPU reference-quality worker
```

- **Browser preview:** a fast WebGPU/WebGL approximation for immediate controls and composition.
- **Export worker:** deterministic CPU rendering for both required output sizes.
- **Reference-quality mode:** optional GPU-backed Kerr ray tracing and adaptive sampling.
- **Metadata:** every render records parameters, source background, algorithm version, preset, and physical/artistic choices.

## Controls

Gravitas will expose spin, inclination, yaw, pitch, roll, field of view, disk inner/outer radius, disk temperature, emissivity profile, spectral index, disk thickness, jet overlay, background source, lensing quality, palette, and seed.

The blue palette requested for Douglas is a selectable color mapping. Physically derived blue coloration from temperature and redshift is recorded separately from artistic palette transforms.

## Documentation

- [Requirements](docs/requirements.md)
- [Research sources and validation](docs/research/sources.md)
- [Rendering algorithms](docs/algorithms/rendering.md)
- [Schwarzschild raster baseline](docs/algorithms/schwarzschild-baseline.md)
- [Azure implementation plan](docs/plans/2026-08-13-azure-web-app.md)
- [Feature priorities](docs/feature-priorities.md)

## Scientific guardrails

- A broad bright EHT ring is not automatically a photon ring.
- Inclined disks should show Doppler-driven brightness asymmetry by default.
- Fast previews are labeled approximations; only the reference path is a general-relativistic ray-tracing model.
- NASA Webb/Hubble backgrounds retain source and crop provenance.
