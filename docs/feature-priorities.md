# Gravitas Feature Priorities

## Scoring

- **Effect:** expected impact on wallpaper quality, user value, or scientific credibility.
- **Complexity:** engineering and computational effort, including validation burden.
- **Priority:** recommended sequence, not a claim that lower-priority work lacks value.

## Delivered MVP

| Feature | Effect | Complexity | Status | Notes |
|---|---|---:|---|---|
| Dual PNG export | High | Low | Delivered | One action creates 5120×1440 and 3440×1440 wallpapers. |
| Live canvas preview | High | Medium | Delivered | Fast browser approximation for interactive composition. |
| Shared spin/disk-axis inclination | High | Low | Delivered | Maintains the aligned thin-disk model. |
| Observer orbit | Medium | Low | Delivered | Rotates the shared viewing frame and Doppler-bright side. |
| Field-of-view zoom | High | Low | Delivered | Reframes the compact scene and star field together. |
| Spin | Medium | Low | Delivered | Preview cue only; not a Kerr-geodesic calculation. |
| Disk temperature scale | Medium | Low | Delivered | Brightness proxy; not a thermal radiative-transfer solution. |
| Blue-spectrum visualization | High | Low | Delivered | A declared visual mapping, not a direct observation. |
| Inner disk radius | High | Low | Delivered | Fast preview changes disk extent; reference mode should tie it to ISCO/truncation physics. |
| Emissivity slope | Medium | Low | Delivered | Fast preview brightness proxy. |
| Disk thickness H/R | Medium | Low | Delivered | Fast preview changes apparent disk width. |
| Prograde/retrograde flow | Medium | Low | Delivered | Reverses the preview Doppler-bright side. |
| Jet strength | Medium | Low | Delivered | Optional visual jet proxy. |
| Magnetic state: SANE/MAD | Medium | Medium | Delivered as metadata | Requires GRMHD-backed rendering before it affects output. |
| Observing band | High | Medium | Delivered as metadata | Requires radiative transfer before it affects output. |

## Priority 1 — Make exported images trustworthy

| Feature | Effect | Complexity | Rationale |
|---|---|---:|---|
| JSON provenance sidecars | High | Low | Record every parameter, seed, algorithm mode, and output size. |
| NASA Webb/Hubble background selection | High | Medium | Meets the cosmic-imaging requirement with source and crop provenance. |
| Physically bounded disk presets | High | Medium | Make M87*-informed, Sgr A*-informed, and generic Kerr settings coherent. |
| Correct export framing | High | Medium | Ensure independent 32:9 and 43:18 framing without stretched composition. |

## Priority 2 — Improve scientific fidelity

| Feature | Effect | Complexity | Rationale |
|---|---:|---:|---|
| Kerr backwards ray tracing | Very high | Very high | Replaces visual proxies with geodesic-based lensing, horizon capture, and disk intersections. |
| Relativistic redshift and Doppler transfer | Very high | High | Implements ray-specific `g` factors rather than brightness heuristics. |
| Background lensing | High | High | Lenses source imagery consistently through the same scene geometry. |
| ISCO derived from spin and flow direction | High | Medium | Connects disk inner radius to Kerr parameters. |
| Continuous temperature/emissivity profile | High | High | Converts disk-temperature controls into a modelled radial emission profile. |

## Priority 3 — Reference-quality research mode

| Feature | Effect | Complexity | Rationale |
|---|---:|---:|---|
| GRMHD snapshot support | Very high | Very high | Lets SANE/MAD settings use simulated plasma structure instead of labels. |
| Polarized radiative transfer | High | Very high | Supports Stokes parameters and Faraday rotation. |
| Observing-frequency transfer | High | High | Makes 230 GHz and optical views physically distinct. |
| Photon subring diagnostics | Medium | Very high | Educational/research visualizations; not a default wallpaper control. |
| GPU render worker | High | High | Enables high-resolution reference-quality exports at acceptable latency. |

## Deferred by design

| Feature | Reason |
|---|---|
| Independent disk and black-hole tilts | Requires a warped or precessing-disk model; invalid for the aligned thin-disk MVP. |
| Literal EHT image recreation | EHT images are reconstruction products and model-dependent; Gravitas should provide informed scenes, not claim observational reproduction. |
| Unlabeled artistic color treatments | All nonphysical palette transforms must remain explicit in metadata and UI copy. |
