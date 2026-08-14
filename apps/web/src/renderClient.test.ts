import { describe, expect, it, vi } from 'vitest'

import { defaultSceneConfig } from './sceneConfig'
import {
  fetchRenderFile,
  renderOutputFilename,
  renderOutputLabel,
  requestWallpapers,
  toRenderRequest,
} from './renderClient'

describe('requestWallpapers', () => {
  it('submits every scene control and polls until API download URLs are ready', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ job_id: 'job-1', status: 'queued' }), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ job_id: 'job-1', status: 'rendering' })))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        job_id: 'job-1',
        output_urls: ['https://api/renders/job-1/files/one.png', 'https://api/renders/job-1/files/two.png'],
        status: 'complete',
      })))
    const stages: string[] = []

    const urls = await requestWallpapers(
      defaultSceneConfig,
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
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({
      axis_inclination_degrees: 30,
      background: 'deep-space',
      blue_spectrum: true,
      disk_temperature: 25_000_000,
      disk_thickness: 0.1,
      emissivity_slope: 3,
      flow_direction: 'prograde',
      inner_disk_radius: 6,
      jet_strength: 0,
      magnetic_state: 'sane',
      mass: 1,
      observing_band: '230-ghz',
      orbit_degrees: 0,
      seed: 42,
      spin: 0.7,
      zoom: 1,
    })
    expect(stages).toEqual(['queued', 'rendering', 'complete'])
    expect(urls).toEqual([
      'https://api/renders/job-1/files/one.png',
      'https://api/renders/job-1/files/two.png',
    ])
  })

  it('serializes distinct scene configs to distinct complete request JSON', () => {
    const first = toRenderRequest(defaultSceneConfig)
    const second = toRenderRequest({
      ...defaultSceneConfig,
      blueSpectrum: false,
      flowDirection: 'retrograde',
      orbitDegrees: 180,
      seed: 73,
      zoom: 2.5,
    })

    expect(first).not.toEqual(second)
    expect(second).toMatchObject({
      blue_spectrum: false,
      flow_direction: 'retrograde',
      orbit_degrees: 180,
      seed: 73,
      zoom: 2.5,
    })
    expect(second).not.toHaveProperty('field_of_view')
    expect(Object.keys(second)).toHaveLength(16)
  })

  it('labels each explicit output link by its rendered dimensions', () => {
    expect(renderOutputLabel('https://api/renders/job/files/gravitas-job-5120x1440.png'))
      .toBe('Download 5120×1440')
    expect(renderOutputLabel('https://api/renders/job/files/gravitas-job-3440x1440.png'))
      .toBe('Download 3440×1440')
    expect(renderOutputFilename('https://api/renders/job/files/gravitas-job-3440x1440.png'))
      .toBe('gravitas-job-3440x1440.png')
  })

  it('fetches a private proxy render into a locally downloadable blob', async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(
      new Blob(['png bytes'], { type: 'image/png' }),
      {
        headers: {
          'Content-Disposition': 'attachment; filename="gravitas-job-5120x1440.png"',
          'Content-Type': 'image/png',
        },
      },
    ))

    const file = await fetchRenderFile(
      'https://api/renders/job/files/gravitas-job-5120x1440.png',
      fetcher,
    )

    expect(file.filename).toBe('gravitas-job-5120x1440.png')
    expect(file.blob.type).toBe('image/png')
    expect(await file.blob.text()).toBe('png bytes')
  })
})
