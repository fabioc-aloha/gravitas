import type { SceneConfig } from './sceneConfig'

export function buildModelFormulas(config: SceneConfig) {
  const temperature = (config.diskTemperature / 1_000_000).toFixed(0)
  const slope = config.emissivitySlope.toFixed(1)
  const thickness = config.diskThickness.toFixed(2)
  const zoom = config.zoom.toFixed(1)

  return [
    {
      expression: 'I_{\\mathrm{obs}} = g^{3 + \\alpha} I_{\\mathrm{emit}}',
      note: 'Observed intensity is transferred by the redshift factor g and spectral index α.',
      title: 'Relativistic transfer',
    },
    {
      expression: `T(r) = ${temperature}\\,\\mathrm{MK}\\left(\\frac{r}{${config.innerDiskRadius}\\,r_g}\\right)^{-${slope}}`,
      note: 'Preview proxy for a radial temperature/emissivity profile.',
      title: 'Disk temperature profile',
    },
    {
      expression: `r_{\\mathrm{in}} = ${config.innerDiskRadius}\\,r_g \\ge r_{\\mathrm{ISCO}}(a_* = ${config.spin.toFixed(3)},\\,${config.flowDirection})`,
      note: 'Reference rendering should constrain the inner edge using Kerr ISCO physics.',
      title: 'Inner disk boundary',
    },
    {
      expression: `\\frac{H}{R} = ${thickness}`,
      note: 'A larger H/R produces a geometrically thicker accretion flow.',
      title: 'Disk geometry',
    },
    {
      expression: `\\theta_{\\mathrm{FOV}} = \\frac{\\theta_0}{${zoom}}`,
      note: 'Zoom narrows the field of view; it does not change black-hole physics.',
      title: 'Camera framing',
    },
  ]
}
