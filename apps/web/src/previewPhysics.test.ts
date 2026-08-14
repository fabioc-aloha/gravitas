import { describe, expect, it } from 'vitest'

import {
  dopplerAsymmetry,
  fieldOfViewForZoom,
  observerOrbitRadians,
} from './previewPhysics'

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

  it('uses the same 48M vertical field as the server renderer', () => {
    expect(fieldOfViewForZoom(1)).toBe(48)
    expect(fieldOfViewForZoom(0.5)).toBe(96)
  })
})
