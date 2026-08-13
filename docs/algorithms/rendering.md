# Rendering Algorithms

## Pipeline

1. Load and validate render configuration.
2. Create a camera basis from yaw, pitch, roll, inclination, field of view, and observer distance.
3. Load/crop the selected cosmic background independently for each target aspect ratio.
4. For every output pixel, trace a backwards ray from camera through the Kerr scene.
5. Classify the ray as horizon capture, disk intersection, or background escape.
6. Compute redshift and observed disk intensity for disk intersections.
7. Sample the lensed background for escaping rays.
8. Tone-map and export both resolutions plus metadata.

## Screen and geodesic setup

For a screen coordinate `(x, y)`, construct a camera ray and convert it to conserved Kerr quantities `(lambda, eta)`. For a distant observer at inclination `theta_o`:

```text
alpha = -lambda / sin(theta_o)
beta  = +/- sqrt(eta + a^2 cos(theta_o)^2 - lambda^2 cot(theta_o)^2)
```

Integrate the null geodesic backwards until it crosses the disk, reaches the horizon, or escapes the scene. The high-fidelity path uses numerical integration; the fast path uses a calibrated critical-curve and lensing approximation.

## Disk emission

Use a configurable radial profile `epsilon(r)` beginning at the selected inner radius:

```text
I_emit(r) = epsilon(r) * blackbody_or_synchrotron(T(r), nu)
T(r) = T_scale * (r / r_inner)^(-p)
```

Apply the ray-specific redshift factor:

```text
I_obs = g^(3 + alpha) * I_emit
nu_obs = g * nu_emit
T_obs = g * T_emit
```

The implementation records whether the visible color comes from this physical path or an artistic palette transform.

## Critical curve and lensing

For the high-fidelity path, determine the Kerr critical curve using spherical photon orbit conditions `R(r)=0` and `R'(r)=0`. Apply adaptive oversampling near the critical curve, then downsample with a high-quality filter. The fast path must label its ring as an approximation and never advertise it as a directly simulated photon ring.

## Perspective

Apply yaw, pitch, and roll before transforming the ray to the black-hole frame. Inclination remains a physical disk-observer angle; camera pitch changes the visual composition. The UI must expose both rather than treating them as interchangeable.
