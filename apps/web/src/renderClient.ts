export type RenderStage = 'queued' | 'rendering' | 'complete' | 'failed'

import type { SceneConfig } from './sceneConfig'

export type RenderRequest = {
  axis_inclination_degrees: number
  background: SceneConfig['background']
  blue_spectrum: boolean
  disk_thickness: number
  disk_temperature: number
  emissivity_slope: number
  flow_direction: SceneConfig['flowDirection']
  inner_disk_radius: number
  jet_strength: number
  magnetic_state: SceneConfig['magneticState']
  mass: number
  observing_band: SceneConfig['observingBand']
  orbit_degrees: number
  seed: number
  spin: number
  zoom: number
}

type RenderResponse = {
  job_id: string
  status: RenderStage
  output_urls?: string[]
}

type Fetch = typeof fetch

const renderApiUrl = import.meta.env.VITE_RENDER_API_URL || '/api'

export function renderOutputLabel(url: string): string {
  const match = url.match(/-(\d+)x(\d+)\.png(?:$|\?)/)
  return match ? `Download ${match[1]}×${match[2]}` : 'Download wallpaper'
}

export function renderOutputFilename(url: string): string {
  return new URL(url).pathname.split('/').at(-1) ?? 'gravitas-wallpaper.png'
}

export async function fetchRenderFile(
  url: string,
  fetcher: Fetch = fetch,
): Promise<{ blob: Blob; filename: string }> {
  const response = await fetcher(url)
  if (!response.ok) throw new Error('Could not download the rendered wallpaper.')
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const filenameMatch = disposition.match(/filename="([^"]+)"/)
  const fallbackName = renderOutputFilename(url)
  return {
    blob: await response.blob(),
    filename: filenameMatch?.[1] ?? fallbackName,
  }
}

export function toRenderRequest(config: SceneConfig): RenderRequest {
  return {
    axis_inclination_degrees: config.axisInclinationDegrees,
    background: config.background,
    blue_spectrum: config.blueSpectrum,
    disk_thickness: config.diskThickness,
    disk_temperature: config.diskTemperature,
    emissivity_slope: config.emissivitySlope,
    flow_direction: config.flowDirection,
    inner_disk_radius: config.innerDiskRadius,
    jet_strength: config.jetStrength,
    magnetic_state: config.magneticState,
    mass: 1,
    observing_band: config.observingBand,
    orbit_degrees: config.orbitDegrees,
    seed: config.seed,
    spin: config.spin,
    zoom: config.zoom,
  }
}

export async function requestWallpapers(
  config: SceneConfig,
  onStage: (stage: RenderStage) => void,
  fetcher: Fetch = fetch,
  wait: (milliseconds: number) => Promise<void> = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds)),
  apiUrl = renderApiUrl,
  signIn: () => void = () => {
    const returnUrl = encodeURIComponent(window.location.href)
    window.location.assign(`/.auth/login/aad?post_login_redirect_uri=${returnUrl}`)
  },
): Promise<string[]> {
  if (!apiUrl) throw new Error('VITE_RENDER_API_URL is required for wallpaper downloads.')
  const baseUrl = apiUrl.replace(/\/$/, '')
  const created = await fetcher(`${baseUrl}/renders`, {
    body: JSON.stringify(toRenderRequest(config)),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  })
  if (created.status === 401) {
    signIn()
    throw new Error('Sign in is required to create wallpapers.')
  }
  if (created.status === 429) throw new Error('Daily render quota reached. Try again tomorrow.')
  if (!created.ok) throw new Error('Could not queue the server render.')
  const job = await created.json() as RenderResponse
  onStage(job.status)

  while (job.status !== 'complete') {
    if (job.status === 'failed') throw new Error('The server render failed.')
    await wait(1_000)
    const response = await fetcher(`${baseUrl}/renders/${job.job_id}`)
    if (!response.ok) throw new Error('Could not check the server render status.')
    const next = await response.json() as RenderResponse
    job.status = next.status
    job.output_urls = next.output_urls
    onStage(job.status)
  }

  if (!job.output_urls?.length) throw new Error('The completed render has no download URLs.')
  return job.output_urls
}
