import { describe, expect, it } from 'vitest'

import { createRenderPlan, defaultSceneConfig } from './sceneConfig'

describe('createRenderPlan', () => {
  it('uses a shared spin and disk axis with observer orbit', () => {
    expect(defaultSceneConfig).toMatchObject({
      axisInclinationDegrees: 30,
      orbitDegrees: 0,
      zoom: 1,
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
      axisInclinationDegrees: 85,
      diskTemperature: 100_000_000,
      orbitDegrees: 180,
      spin: 0.998,
    })

    expect(plan.config).toMatchObject({
      axisInclinationDegrees: 85,
      diskTemperature: 100_000_000,
      orbitDegrees: 180,
      spin: 0.998,
    })
  })
})
