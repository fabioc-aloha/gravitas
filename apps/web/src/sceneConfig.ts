export type SceneConfig = {
  background: 'procedural-stars' | 'deep-space'
  blueSpectrum: boolean
  diskTemperature: number
  inclinationDegrees: number
  pitchDegrees: number
  seed: number
  spin: number
  yawDegrees: number
}

export const defaultSceneConfig: SceneConfig = {
  background: 'deep-space',
  blueSpectrum: true,
  diskTemperature: 25_000_000,
  inclinationDegrees: 30,
  pitchDegrees: 0,
  seed: 42,
  spin: 0.7,
  yawDegrees: 0,
}

export const outputSizes = [
  { height: 1440, width: 5120 },
  { height: 1440, width: 3440 },
] as const

export function createRenderPlan(config: SceneConfig) {
  if (config.spin < 0 || config.spin > 0.998) throw new RangeError('Spin must be from 0 to 0.998.')
  if (config.inclinationDegrees < 0 || config.inclinationDegrees > 85) {
    throw new RangeError('Inclination must be from 0 to 85 degrees.')
  }
  if (config.diskTemperature < 1_000 || config.diskTemperature > 100_000_000) {
    throw new RangeError('Disk temperature must be from 1,000 K to 100,000,000 K.')
  }

  return { config, outputs: [...outputSizes] }
}
