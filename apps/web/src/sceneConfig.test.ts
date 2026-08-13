import { describe, expect, it } from 'vitest'

import { createRenderPlan, defaultSceneConfig } from './sceneConfig'

describe('createRenderPlan', () => {
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
      diskTemperature: 100_000_000,
      inclinationDegrees: 85,
      spin: 0.998,
    })

    expect(plan.config).toMatchObject({
      diskTemperature: 100_000_000,
      inclinationDegrees: 85,
      spin: 0.998,
    })
  })
})
