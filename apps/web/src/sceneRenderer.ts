import type { SceneConfig } from './sceneConfig'
import { dopplerAsymmetry, observerOrbitRadians } from './previewPhysics'

const webbBackground = new Image()
webbBackground.src = '/backgrounds/webb-carina.webp'

const backgroundReady = new Promise<void>((resolve, reject) => {
  webbBackground.addEventListener('load', () => resolve(), { once: true })
  webbBackground.addEventListener('error', () => reject(new Error('Could not load Webb background.')), { once: true })
})

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

export async function renderScene(canvas: HTMLCanvasElement, config: SceneConfig) {
  const context = canvas.getContext('2d')
  if (!context) return
  await backgroundReady

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
  const diskWidth = scale * (0.4 - config.innerDiskRadius * 0.008)
  const blue = config.blueSpectrum ? '#4da6ff' : accent

  context.fillStyle = background
  context.fillRect(0, 0, width, height)

  const sourceRatio = webbBackground.naturalWidth / webbBackground.naturalHeight
  const targetRatio = width / height
  const sourceWidth = sourceRatio > targetRatio ? webbBackground.naturalHeight * targetRatio : webbBackground.naturalWidth
  const sourceHeight = sourceRatio > targetRatio ? webbBackground.naturalHeight : webbBackground.naturalWidth / targetRatio
  const sourceX = (webbBackground.naturalWidth - sourceWidth) / 2
  const sourceY = (webbBackground.naturalHeight - sourceHeight) / 2
  context.globalAlpha = config.background === 'deep-space' ? 0.78 : 0.34
  context.drawImage(webbBackground, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, width, height)
  context.globalAlpha = 1

  const sky = context.createRadialGradient(centerX, centerY, 0, centerX, centerY, width * 0.65 / config.zoom)
  sky.addColorStop(0, rgba(blue, 0.15))
  sky.addColorStop(0.5, rgba(blue, 0.045))
  sky.addColorStop(1, 'transparent')
  context.fillStyle = sky
  context.fillRect(0, 0, width, height)

  const stars = config.background === 'deep-space' ? 180 : 80
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
  const approachingSide = (Math.cos(orbit) >= 0 ? 1 : -1) * (config.flowDirection === 'prograde' ? 1 : -1)
  const beamedOpacity = 0.2 + temperature * beaming * (0.25 + config.emissivitySlope * 0.08)
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
  context.lineWidth = scale * (0.025 + config.diskThickness * 0.35)
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
  if (config.jetStrength > 0) {
    context.save()
    context.translate(centerX, centerY)
    context.rotate(orbit)
    context.strokeStyle = rgba(blue, 0.15 + config.jetStrength * 0.55)
    context.lineWidth = scale * 0.01
    context.filter = `blur(${scale * 0.006}px)`
    context.beginPath()
    context.moveTo(0, -shadowRadius * 0.6)
    context.lineTo(0, -scale * (0.12 + config.jetStrength * 0.35))
    context.moveTo(0, shadowRadius * 0.6)
    context.lineTo(0, scale * (0.12 + config.jetStrength * 0.35))
    context.stroke()
    context.restore()
  }

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
