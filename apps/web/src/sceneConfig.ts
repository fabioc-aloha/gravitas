export type SceneConfig = {
  background: 'procedural-stars' | 'deep-space'
  blackHoleInclinationDegrees: number
  blueSpectrum: boolean
  diskInclinationDegrees: number
  diskTemperature: number
  orbitDegrees: number
  pitchDegrees: number
  seed: number
  spin: number
}

export const defaultSceneConfig: SceneConfig = {
  background: 'deep-space',
  blackHoleInclinationDegrees: 0,
  blueSpectrum: true,
  diskInclinationDegrees: 30,
  diskTemperature: 25_000_000,
  orbitDegrees: 0,
  pitchDegrees: 0,
  seed: 42,
  spin: 0.7,
}

export const outputSizes = [
  { height: 1440, width: 5120 },
  { height: 1440, width: 3440 },
] as const

export function createRenderPlan(config: SceneConfig) {
  if (config.spin < 0 || config.spin > 0.998) throw new RangeError('Spin must be from 0 to 0.998.')
  if (config.diskInclinationDegrees < 0 || config.diskInclinationDegrees > 85) {
    throw new RangeError('Disk inclination must be from 0 to 85 degrees.')
  }
  if (config.blackHoleInclinationDegrees < 0 || config.blackHoleInclinationDegrees > 85) {
    throw new RangeError('Black-hole inclination must be from 0 to 85 degrees.')
  }
  if (config.diskTemperature < 1_000 || config.diskTemperature > 100_000_000) {
    throw new RangeError('Disk temperature must be from 1,000 K to 100,000,000 K.')
  }

  return { config, outputs: [...outputSizes] }
}
