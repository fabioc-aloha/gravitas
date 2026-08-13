import type { SceneConfig } from './sceneConfig'
import { dopplerAsymmetry, observerOrbitRadians } from './previewPhysics'

function random(seed: number) {
  let state = seed >>> 0
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0
    return state / 2 ** 32
  }
}

function rgba(hex: string, opacity: number) {
  const value = hex.trim().replace('#', '')
  const red = Number.parseInt(value.slice(0, 2), 16)
  const green = Number.parseInt(value.slice(2, 4), 16)
  const blue = Number.parseInt(value.slice(4, 6), 16)
  return `rgba(${red}, ${green}, ${blue}, ${opacity})`
}

export function renderScene(canvas: HTMLCanvasElement, config: SceneConfig) {
  const context = canvas.getContext('2d')
  if (!context) return

  const { width, height } = canvas
  const style = getComputedStyle(document.documentElement)
  const accent = style.getPropertyValue('--cp-accent').trim()
  const text = style.getPropertyValue('--cp-text').trim()
  const background = style.getPropertyValue('--cp-bg').trim()
  const rand = random(config.seed)
  const centerX = width * 0.52
  const centerY = height * 0.5
  const scale = Math.min(width, height) * config.zoom
  const axisInclination = config.axisInclinationDegrees * Math.PI / 180
  const orbit = observerOrbitRadians(config.orbitDegrees)
  const beaming = dopplerAsymmetry(config.axisInclinationDegrees)
  const diskHeight = Math.max(scale * 0.035, Math.cos(axisInclination) * scale * 0.14)
  const diskWidth = scale * 0.35
  const blue = config.blueSpectrum ? '#4da6ff' : accent

  context.fillStyle = background
  context.fillRect(0, 0, width, height)

  const sky = context.createRadialGradient(centerX, centerY, 0, centerX, centerY, width * 0.65 / config.zoom)
  sky.addColorStop(0, rgba(blue, 0.15))
  sky.addColorStop(0.5, rgba(blue, 0.045))
  sky.addColorStop(1, 'transparent')
  context.fillStyle = sky
  context.fillRect(0, 0, width, height)

  const stars = config.background === 'deep-space' ? 800 : 420
  for (let index = 0; index < stars; index += 1) {
    const x = centerX + (rand() * width - centerX) * config.zoom
    const y = centerY + (rand() * height - centerY) * config.zoom
    const size = rand() * 1.7 + 0.25
    context.fillStyle = rgba(text, 0.15 + rand() * 0.7)
    context.beginPath()
    context.arc(x, y, size, 0, Math.PI * 2)
    context.fill()
  }

  context.save()
  context.translate(centerX, centerY)
  context.rotate(orbit)
  const temperature = Math.min(1, config.diskTemperature / 100_000_000)
  const approachingSide = Math.cos(orbit) >= 0 ? 1 : -1
  const beamedOpacity = 0.2 + temperature * beaming * 0.5
  const diskGradient = context.createLinearGradient(-diskWidth, 0, diskWidth, 0)
  diskGradient.addColorStop(0, rgba(blue, 0.04))
  diskGradient.addColorStop(0.26, rgba(blue, 0.35))
  if (beaming < 0.01) {
    diskGradient.addColorStop(0.5, rgba(text, 0.82))
    diskGradient.addColorStop(0.74, rgba(blue, 0.35))
  } else if (approachingSide > 0) {
    diskGradient.addColorStop(0.5, rgba(text, 0.82))
    diskGradient.addColorStop(0.7, rgba(blue, beamedOpacity))
  } else {
    diskGradient.addColorStop(0.3, rgba(blue, beamedOpacity))
    diskGradient.addColorStop(0.5, rgba(text, 0.82))
  }
  diskGradient.addColorStop(1, rgba(blue, 0.04))
  context.strokeStyle = diskGradient
  context.lineWidth = scale * 0.06
  context.filter = `blur(${Math.max(2, scale * 0.007)}px)`
  context.beginPath()
  context.ellipse(0, 0, diskWidth, diskHeight, 0, 0, Math.PI * 2)
  context.stroke()
  context.filter = 'none'
  context.lineWidth = scale * 0.008
  context.strokeStyle = rgba(text, 0.5)
  context.beginPath()
  context.ellipse(0, 0, diskWidth, diskHeight, 0, 0, Math.PI * 2)
  context.stroke()
  context.restore()

  const shadowRadius = scale * (0.11 + config.spin * 0.015)
  const lens = context.createRadialGradient(centerX, centerY, shadowRadius * 0.8, centerX, centerY, shadowRadius * 1.6)
  lens.addColorStop(0, '#000000')
  lens.addColorStop(0.7, '#000000')
  lens.addColorStop(0.82, rgba(blue, 0.55))
  lens.addColorStop(1, 'transparent')
  context.fillStyle = lens
  context.beginPath()
  context.arc(centerX, centerY, shadowRadius * 1.6, 0, Math.PI * 2)
  context.fill()

  context.save()
  context.translate(centerX, centerY)
  context.fillStyle = '#000000'
  context.beginPath()
  context.arc(0, 0, shadowRadius, 0, Math.PI * 2)
  context.fill()

  context.strokeStyle = rgba(blue, 0.55)
  context.lineWidth = Math.max(1, scale * 0.002)
  context.beginPath()
  context.arc(0, 0, shadowRadius * 1.1, 0, Math.PI * 2)
  context.stroke()
  context.restore()
}
