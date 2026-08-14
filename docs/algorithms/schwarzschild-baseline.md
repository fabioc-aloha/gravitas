# Schwarzschild Reference Raster

Gravitas produces a deterministic CPU reference image of a non-spinning black
hole. It is a visual approximation, **not** a general-relativistic ray-tracing
(GRRT) renderer.

## Implemented model

- **Capture:** far-field rays with screen-plane impact parameter
  `b <= 3 sqrt(3) M` are black. This Schwarzschild critical impact parameter
  is the exact capture boundary used by this raster.
- **Escaped celestial sphere:** every non-captured ray samples a deterministic
  procedural celestial sphere or an aspect-cropped NASA Webb texture. The
  sample's screen coordinate is displaced radially by
  `alpha = 4M / b`, the leading weak-field Schwarzschild deflection term.
  The correction is capped at 1.25 radians near the photon sphere so it cannot
  be mistaken for a strong-field solver.
- **Thin disk:** a direct projected plane has configurable inner/outer radii,
  temperature scale, radial temperature slope, inclination, and Doppler-like
  asymmetry. Its radial profile is
  `T(r) = T0 (r/r_in)^(-p) [1 - sqrt(r_in/r)]^(1/4)` and brightness is
  proportional to `T^4`. The asymmetry is a tunable `sin(azimuth)` boost
  scaled by inclination; it is a visual Doppler proxy.
  The UI's intensity emissivity index `q` is converted to temperature exponent
  `q/4`, so the default `q=3` yields the standard `T proportional to r^-3/4`
  thin-disk scaling rather than an unphysical `I proportional to r^-12`.
- **Repeatability:** the procedural sphere is seeded. `RenderJob.seed`
  forwards the same seed to both service PNG sizes, and defaults to `0`.
  `LocalRenderService` writes `5120x1440` and `3440x1440` PNGs.
- **Aspect preservation:** horizontal screen extent scales with output aspect
  ratio so the Schwarzschild capture boundary remains circular in pixel space.

## Approximation boundaries

The escaped-ray mapping does not integrate null geodesics, solve the
Schwarzschild lens equation, conserve ray bundles, or generate photon rings
and higher-order images. The disk is not intersected by lensed geodesics; it
has no gravitational redshift, transverse Doppler effect, relativistic
beaming, light travel time, self-occultation, or radiative transfer. Disk
defaults use an inner radius of `6M` as a practical non-spinning reference,
but that value is a configurable artistic model parameter rather than an
ISCO/GRRT calculation.

Kerr spin, frame dragging, exact escaped geodesics, geodesic disk
intersections, and relativistic transfer remain out of scope.
