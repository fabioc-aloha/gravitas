import { useEffect, useRef, useState } from 'react'

import { createRenderPlan, defaultSceneConfig, outputSizes, type SceneConfig } from './sceneConfig'
import { renderScene } from './sceneRenderer'

function App() {
  const [config, setConfig] = useState<SceneConfig>(defaultSceneConfig)
  const [isExporting, setIsExporting] = useState(false)
  const previewRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (previewRef.current) renderScene(previewRef.current, config)
  }, [config])

  function update<K extends keyof SceneConfig>(key: K, value: SceneConfig[K]) {
    setConfig((current) => ({ ...current, [key]: value }))
  }

  async function downloadWallpapers() {
    setIsExporting(true)
    const plan = createRenderPlan(config)
    for (const output of plan.outputs) {
      const canvas = document.createElement('canvas')
      canvas.width = output.width
      canvas.height = output.height
      renderScene(canvas, config)
      const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
      if (!blob) continue
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `gravitas-${output.width}x${output.height}.png`
      link.click()
      URL.revokeObjectURL(link.href)
    }
    setIsExporting(false)
  }

  return (
    <main>
      <p className="eyebrow">Scientific cosmic generator</p>
      <h1>Gravitas</h1>
      <p className="tagline">Generative black-hole scenes, grounded in relativity.</p>
      <section className="studio">
        <div className="controls panel">
          <h2>Scene controls</h2>
          <label>Spin <output>{config.spin.toFixed(3)}</output>
            <input type="range" min="0" max="0.998" step="0.001" value={config.spin} onChange={(event) => update('spin', Number(event.target.value))} />
          </label>
          <label>Spin/disk axis inclination <output>{config.axisInclinationDegrees}°</output>
            <input type="range" min="0" max="85" value={config.axisInclinationDegrees} onChange={(event) => update('axisInclinationDegrees', Number(event.target.value))} />
          </label>
          <label>Observer orbit <output>{config.orbitDegrees}°</output>
            <input type="range" min="0" max="360" value={config.orbitDegrees} onChange={(event) => update('orbitDegrees', Number(event.target.value))} />
          </label>
          <label>Zoom <output>{config.zoom.toFixed(1)}×</output>
            <input type="range" min="0.5" max="3" step="0.1" value={config.zoom} onChange={(event) => update('zoom', Number(event.target.value))} />
          </label>
          <label>Disk temperature scale <output>{(config.diskTemperature / 1_000_000).toFixed(0)}M K</output>
            <input type="range" min="1000000" max="100000000" step="1000000" value={config.diskTemperature} onChange={(event) => update('diskTemperature', Number(event.target.value))} />
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={config.blueSpectrum} onChange={(event) => update('blueSpectrum', event.target.checked)} />
            Blue-spectrum visualization
          </label>
          <button type="button" onClick={downloadWallpapers} disabled={isExporting}>
            {isExporting ? 'Generating…' : 'Download both wallpapers'}
          </button>
        </div>
        <div className="preview panel">
          <canvas ref={previewRef} width="1400" height="700" aria-label="Black-hole scene preview" />
          <p>Fast visual approximation. Final downloads include 5120×1440 and 3440×1440 PNGs.</p>
          <dl>
            <div><dt>Physics cues</dt><dd>Projected disk, inclination-driven beaming, and a critical-curve approximation</dd></div>
            <div><dt>Palette note</dt><dd>Blue is a selectable visualization, not a direct observation.</dd></div>
            <div><dt>Model limit</dt><dd>Spin and temperature are preview cues; Kerr ray tracing is planned for reference-quality output.</dd></div>
            <div><dt>Outputs</dt><dd>{outputSizes.map((size) => `${size.width}×${size.height}`).join(' and ')}</dd></div>
          </dl>
        </div>
      </section>
    </main>
  )
}

export default App
