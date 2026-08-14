export type RenderStage = 'queued' | 'rendering' | 'complete' | 'failed'

type RenderRequest = {
  mass: number
  field_of_view: number
}

type RenderResponse = {
  job_id: string
  status: RenderStage
  output_urls?: string[]
}

type Fetch = typeof fetch

const renderApiUrl = import.meta.env.VITE_RENDER_API_URL

export async function requestWallpapers(
  request: RenderRequest,
  onStage: (stage: RenderStage) => void,
  fetcher: Fetch = fetch,
  wait: (milliseconds: number) => Promise<void> = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds)),
  apiUrl = renderApiUrl,
): Promise<string[]> {
  if (!apiUrl) throw new Error('VITE_RENDER_API_URL is required for wallpaper downloads.')
  const baseUrl = apiUrl.replace(/\/$/, '')
  const created = await fetcher(`${baseUrl}/renders`, {
    body: JSON.stringify(request),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  })
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
