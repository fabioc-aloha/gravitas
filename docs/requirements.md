# Requirements Specification

## Product goal

Generate scientifically informed black-hole wallpapers for Douglas. Each render must create both native monitor outputs: `5120x1440` and `3440x1440`.

## Functional requirements

### Output

- Generate PNG outputs for both required dimensions in one render operation.
- Preserve aspect ratio with independent composition framing per output; never stretch pixels.
- Save a JSON sidecar next to each image containing parameters, algorithm version, random seed, date, and research preset.

### Physical model

- Provide a physically informed default based on a Kerr black-hole scene viewed through backwards ray tracing.
- Render a shadow/critical curve, direct disk emission, lensed disk emission, background-star gravitational lensing, gravitational redshift, and relativistic Doppler beaming.
- Do not label the broad bright EHT ring as a photon ring. The product must distinguish direct emission, lensing ring, and photon-ring approximations in metadata and UI copy.
- Clearly mark non-reference visual controls as artistic modifications.

### User-selectable parameters

| Parameter | Range / choices | Default |
|---|---|---|
| Research preset | M87*-informed, Sgr A*-informed, generic Kerr, artistic | Generic Kerr |
| Dimension | Both fixed outputs | 5120x1440 + 3440x1440 |
| Spin `a/M` | 0.0 to 0.998 | 0.0 in Schwarzschild mode |
| Shared spin/disk-axis inclination | 0 to 85 degrees | 30 degrees |
| Observer orbit / azimuth about the shared axis | 0 to 360 degrees | 0 degrees |
| Camera roll | -180 to 180 degrees | 0 degrees |
| Field of view | 5 to 90 degrees | 35 degrees |
| Accretion-disk inner radius | ISCO to 20 gravitational radii | ISCO |
| Accretion-disk outer radius | inner radius + 1 to 100 gravitational radii | 30 gravitational radii |
| Disk temperature scale | 1,000,000 K to 100,000,000 K | visualization proxy until mass/accretion rate are modeled |
| Radial intensity emissivity `q` | 1.0 to 5.0 | 3.0; thermal temperature exponent is `q/4` |
| Disk emissivity profile | GLM-inspired, power law, extended disk | GLM-inspired |
| Spectral index | -2.0 to 2.0 | 0.0 |
| Disk thickness | razor thin to thick | thin |
| Magnetic/jet overlay | off, subtle, research-inspired | off |
| Background | NASA Webb, NASA Hubble, procedural stars, user image | NASA Webb |
| Background lensing | off, fast approximation, ray traced | fast approximation |
| Random seed | integer | generated and recorded |

### Blue-spectrum preference

Douglas may select a blue-dominant palette. The application must present this as a visualization/color-mapping choice, not as evidence that a black hole itself emits blue light. In physically motivated thermal render modes, blue may emerge from hotter approaching disk regions after Doppler shifting; the application must preserve that distinction in metadata.

### Background imagery

- Include cosmic background modes using NASA Webb and Hubble source images that meet a minimum source height of 1440 pixels.
- Store source URL, credit, license/use note, and crop transform in output metadata.
- Apply lensing to background imagery when the selected quality mode supports it.

## Non-functional requirements

- Deterministic output for the same seed and parameters.
- Default render should complete in under 30 seconds at each target size on CPU; high-fidelity mode may take longer and must report progress.
- Keep the fast renderer and reference ray tracer separate. Never claim the fast approximation is an observational simulation.
- Provide automated validation for dimensions, determinism, parameter bounds, and no-stretch framing.

## Acceptance criteria

1. One command generates both required sizes and JSON sidecars.
2. Both images use the selected perspective and matching scientific parameters while retaining independent framing.
3. Inclined-disk presets visibly show asymmetric brightness unless an artistic override is enabled.
4. Research presets cite their source in output metadata.
5. Blue-palette renders are marked as color-mapped unless produced by the physical temperature/redshift pipeline.
