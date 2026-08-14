import { describe, expect, it, vi } from 'vitest'

import { requestWallpapers } from './renderClient'

describe('requestWallpapers', () => {
  it('submits a server render and polls until URLs are ready', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ job_id: 'job-1', status: 'queued' }), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ job_id: 'job-1', status: 'rendering' })))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        job_id: 'job-1',
        output_urls: ['https://downloads/one.png', 'https://downloads/two.png'],
        status: 'complete',
      })))
    const stages: string[] = []

    const urls = await requestWallpapers(
      { field_of_view: 20, mass: 1 },
      (stage) => stages.push(stage),
      fetcher,
      async () => {},
      'https://render.example',
    )

    expect(fetcher.mock.calls.map(([url]) => url)).toEqual([
      'https://render.example/renders',
      'https://render.example/renders/job-1',
      'https://render.example/renders/job-1',
    ])
    expect(stages).toEqual(['queued', 'rendering', 'complete'])
    expect(urls).toEqual(['https://downloads/one.png', 'https://downloads/two.png'])
  })
})
