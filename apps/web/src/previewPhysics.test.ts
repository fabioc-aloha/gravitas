import { describe, expect, it } from 'vitest'

import { dopplerAsymmetry, observerOrbitRadians } from './previewPhysics'

describe('preview physics controls', () => {
  it('has no Doppler-side asymmetry for a face-on aligned disk', () => {
    expect(dopplerAsymmetry(0)).toBe(0)
  })

  it('increases Doppler-side asymmetry as the observer moves toward edge-on', () => {
    expect(dopplerAsymmetry(75)).toBeGreaterThan(dopplerAsymmetry(30))
  })

  it('maps an observer orbit to a continuous full rotation', () => {
    expect(observerOrbitRadians(0)).toBe(0)
    expect(observerOrbitRadians(360)).toBeCloseTo(Math.PI * 2)
  })
})
