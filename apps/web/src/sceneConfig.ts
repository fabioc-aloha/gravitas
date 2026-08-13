export type SceneConfig = {
  axisInclinationDegrees: number
  background: 'procedural-stars' | 'deep-space'
  blueSpectrum: boolean
  diskTemperature: number
  orbitDegrees: number
  seed: number
  spin: number
  zoom: number
}

export const defaultSceneConfig: SceneConfig = {
  axisInclinationDegrees: 30,
  background: 'deep-space',
  blueSpectrum: true,
  diskTemperature: 25_000_000,
  orbitDegrees: 0,
  seed: 42,
  spin: 0.7,
  zoom: 1,
}

export const outputSizes = [
  { height: 1440, width: 5120 },
  { height: 1440, width: 3440 },
] as const

export function createRenderPlan(config: SceneConfig) {
  if (config.spin < 0 || config.spin > 0.998) throw new RangeError('Spin must be from 0 to 0.998.')
  if (config.axisInclinationDegrees < 0 || config.axisInclinationDegrees > 85) {
    throw new RangeError('Axis inclination must be from 0 to 85 degrees.')
  }
  if (config.diskTemperature < 1_000 || config.diskTemperature > 100_000_000) {
    throw new RangeError('Disk temperature must be from 1,000 K to 100,000,000 K.')
  }
  if (config.zoom < 0.5 || config.zoom > 3) {
    throw new RangeError('Zoom must be from 0.5 to 3.')
  }

  return { config, outputs: [...outputSizes] }
}
