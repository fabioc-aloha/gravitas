import { describe, expect, it } from 'vitest'

import { buildModelFormulas } from './formulas'
import { defaultSceneConfig } from './sceneConfig'

describe('model formulas', () => {
  it('includes the documented redshift and emissivity relationships', () => {
    const formulas = buildModelFormulas({
      ...defaultSceneConfig,
      diskTemperature: 32_000_000,
      emissivitySlope: 2.5,
      innerDiskRadius: 8,
      zoom: 1.7,
    })

    expect(formulas.map((formula) => formula.expression)).toEqual(
      expect.arrayContaining([
        'I_{\\mathrm{obs}} = g^{3 + \\alpha} I_{\\mathrm{emit}}',
        'T(r) = 32\\,\\mathrm{MK}\\left(\\frac{r}{8\\,r_g}\\right)^{-2.5}',
      ]),
    )
  })
})
