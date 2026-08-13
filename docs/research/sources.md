# Research Basis and Validation Notes

## Scope

This document records the sources that validate the renderer requirements. It does not turn an observation into a claim of exact reproduction: observed EHT images are resolution-limited, model-dependent reconstructions.

## Primary references

| Topic | Source | Implementation consequence |
|---|---|---|
| Kerr lensing and subrings | Gralla & Lupsasca, *Lensing by Kerr Black Holes* (2020), https://arxiv.org/abs/1910.12873 | Use backwards null-geodesic tracing for reference rendering and distinguish direct, lensing, and photon-ring paths. |
| Film-quality lensing renderer and known simplifications | James et al., *Gravitational Lensing by Spinning Black Holes...* (2015), https://arxiv.org/abs/1502.03808 | Use it as a ray-bundle/lensing reference; do not reproduce its intentionally non-Doppler-shifted disk as physics. |
| M87* first image | EHT Collaboration, *ApJL* 875 L1/L4/L5 (2019), https://arxiv.org/abs/1906.11238 | M87*-informed preset uses an asymmetric thick emission ring, not a literal thin photon ring. |
| Sgr A* first image | EHT Collaboration, *ApJL* 930 L12 (2022; arXiv record 2023), https://arxiv.org/abs/2311.08680 | Sgr A*-informed preset uses a thick ring, dim interior, modest asymmetry, and low-to-moderate inclination. |
| Photon-ring science limits | Black Hole Explorer science case (2024), https://www.blackholeexplorer.org/ | Current EHT bright rings should not be conflated with directly resolved photon rings. |
| Open reference renderer | GYOTO 2.0, https://gyoto.obspm.fr/ | Optional high-fidelity validation target for selected scenes. |

## Validated presentation rules

- The observed intensity transforms approximately as `I_obs = g^(3 + alpha) I_emit`, where `g` is the redshift factor and `alpha` is spectral index.
- Doppler beaming brightens the approaching side of a rotating disk; a uniform disk is an artistic simplification.
- The Kerr critical curve is nearly circular for low inclinations and can become asymmetric at high spin/inclination.
- A color palette is not itself a measurement. Blue spectral coloration must be presented as either temperature/redshift-derived or a chosen visualization mapping.
- The baseline UI assumes an aligned Kerr spin axis and thin-disk angular-momentum axis. Independent tilt controls require a warped or precessing-disk model and are therefore not exposed in the MVP.
- MVP control audit: shared-axis inclination changes projected disk aspect ratio and Doppler-asymmetry strength; observer orbit changes the common scene position angle; zoom changes the field framing. Spin, temperature, and lensing remain explicitly labeled preview approximations until the Kerr ray-tracing path is implemented.

## NASA background provenance

Use only official NASA gallery assets that satisfy the source-resolution requirement. Save each source URL, credit text, and crop transform. Relevant galleries:

- https://science.nasa.gov/mission/webb/multimedia/images/
- https://www.nasa.gov/missions/webb/james-webb-space-telescope-video-and-image-gallery/
- https://science.nasa.gov/mission/hubble/multimedia/hubble-images/
