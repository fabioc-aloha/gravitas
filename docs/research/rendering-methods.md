# Rendering Methods and Open-Source Evaluation

## Decision summary

Gravitas should use a three-tier rendering strategy:

1. **Interactive preview:** custom, browser-side approximation driven by a precomputed Kerr lensing lookup table.
2. **Production raster export:** a custom CPU renderer using semi-analytic Kerr geodesics, a Novikov-Thorne-inspired thin disk, a real celestial-sphere background, and explicit provenance.
3. **Reference validation:** offline EHT-grade GRRT renders from ipole or GYOTO to measure approximation error, not to claim observational reproduction.

## Rendering approaches

| Approach | Strength | Limitation | Gravitas role |
|---|---|---|---|
| Numeric Kerr geodesic integration | General and physically expressive | Thousands of integration steps per ray can be expensive | Reference mode and validation |
| Semi-analytic Kerr geodesics | Fast and exact for stationary Kerr metrics | Less flexible outside Kerr | Preferred production/export path |
| Screen-space approximation | Interactive and inexpensive | Cannot claim physical accuracy | Current composition preview only |
| GRMHD transfer | Highest physical realism | Requires simulation snapshots and substantial compute | Future research-quality tier |

## Natural visual rendering stack

### Accretion flow

Use a Novikov-Thorne-inspired thin-disk profile before introducing GRMHD data:

```text
T(r) ∝ (r - r_in)^(1/2) r^(-7/4)
I_obs = g^(3 + α) I_emit
```

Tie `r_in` to the Kerr ISCO for the selected spin and flow direction in reference-quality mode. Keep manual disk radius as an explicitly artistic or exploratory override.

### Background and lensing

Use a real celestial-sphere texture, then map escaped photon rays to the source sphere. Recommended source options:

- ESO Milky Way panorama (verify current reuse terms before packaging).
- 2MASS all-sky data, subject to its data-use guidance.
- NASA Webb/Hubble imagery with source URL, credit, crop transform, and use note stored in output metadata.

Procedural star layers may supplement the source texture for density and seed-controlled variation, but should not replace the real background in natural-scene mode.

### Tone mapping

- Convert thermal disk output using blackbody temperature to a display color space where applicable.
- Apply an HDR-to-LDR transform after radiative transfer: ACES for cinematic appearance or logarithmic/gamma mapping for EHT-style visualization.
- Preserve a clear metadata flag for physical-color versus artistic-palette output.

## Open-source software evaluation

| Project | License | Suitability | Recommendation |
|---|---|---|---|
| [ipole](https://github.com/AFD-Illinois/ipole) | BSD-3-Clause | CPU/OpenMP GRRT, EHT comparison validation, container-friendly | Adopt for offline validation and reference render corpus |
| [GYOTO](https://github.com/gyoto/Gyoto) | GPL-3.0 | Kerr metrics, thin/thick disks, polarized transfer, Python bindings | Use as an isolated validation subprocess/service; assess GPL implications before distribution |
| [Odyssey](https://github.com/hungyipu/Odyssey) | GPL stated by project | CUDA Kerr geodesics | Future GPU tier only |
| RAPTOR | No public license identified | Useful code reference | Do not copy, redistribute, or integrate |
| grtrans | No public license identified | Semi-analytic geodesic reference | Do not integrate without license clearance |
| starless | No public license identified | Educational Schwarzschild prototype | Do not integrate without license clearance |

## Validation sources

- Gralla & Lupsasca, *Lensing by Kerr Black Holes* (2020): https://arxiv.org/abs/1910.12873
- EHT Collaboration, M87* physical origin of the asymmetric ring (2019): https://arxiv.org/abs/1906.11242
- EHT Collaboration, Sgr A* shadow result (2022): https://arxiv.org/abs/2311.08680
- ipole repository: https://github.com/AFD-Illinois/ipole
- GYOTO repository: https://github.com/gyoto/Gyoto

## Guardrails

- Do not call an EHT-like bright ring a directly resolved photon ring.
- Do not treat a stylized blue palette as an observed black-hole color.
- Keep preview, production, and reference-quality modes distinct in UI and metadata.
- Verify upstream license terms again before each dependency adoption or asset distribution.
