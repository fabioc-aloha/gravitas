import type { SceneConfig } from './sceneConfig'

export function buildModelFormulas(config: SceneConfig) {
  const temperature = (config.diskTemperature / 1_000_000).toFixed(0)
  const slope = config.emissivitySlope.toFixed(1)
  const temperatureSlope = (config.emissivitySlope / 4).toFixed(3)
  const thickness = config.diskThickness.toFixed(2)
  const zoom = config.zoom.toFixed(1)

  return [
    {
      expression: 'I_{\\mathrm{obs}} = g^{3 + \\alpha} I_{\\mathrm{emit}}',
      note: 'Observed intensity is transferred by the redshift factor g and spectral index α.',
      title: 'Relativistic transfer',
    },
    {
      expression: `I_{\\mathrm{emit}}(r) \\propto \\left(\\frac{r}{${config.innerDiskRadius}\\,r_g}\\right)^{-${slope}},\\quad T(r) \\propto \\left(\\frac{r}{${config.innerDiskRadius}\\,r_g}\\right)^{-${temperatureSlope}}`,
      note: `For thermal emission I∝T⁴, so emissivity q=${slope} maps to temperature exponent q/4=${temperatureSlope}. The ${temperature} MK value remains a visualization proxy until mass and accretion rate are modelled.`,
      title: 'Disk emission profile',
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
