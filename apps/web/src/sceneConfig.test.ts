import { describe, expect, it } from 'vitest'

import { createRenderPlan, defaultSceneConfig } from './sceneConfig'

describe('createRenderPlan', () => {
  it('provides independent disk, black-hole, and orbit orientation controls', () => {
    expect(defaultSceneConfig).toMatchObject({
      blackHoleInclinationDegrees: 0,
      diskInclinationDegrees: 30,
      orbitDegrees: 0,
    })
  })

  it('always creates both required wallpaper sizes', () => {
    const plan = createRenderPlan(defaultSceneConfig)

    expect(plan.outputs).toEqual([
      { height: 1440, width: 5120 },
      { height: 1440, width: 3440 },
    ])
  })

  it('keeps scene values within their physical control bounds', () => {
    const plan = createRenderPlan({
      ...defaultSceneConfig,
      blackHoleInclinationDegrees: 70,
      diskTemperature: 100_000_000,
      diskInclinationDegrees: 85,
      orbitDegrees: 180,
      spin: 0.998,
    })

    expect(plan.config).toMatchObject({
      blackHoleInclinationDegrees: 70,
      diskTemperature: 100_000_000,
      diskInclinationDegrees: 85,
      orbitDegrees: 180,
      spin: 0.998,
    })
  })
})
