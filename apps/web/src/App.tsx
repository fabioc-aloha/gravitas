import { useEffect, useRef, useState } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'

import { defaultSceneConfig, outputSizes, type SceneConfig } from './sceneConfig'
import { buildModelFormulas } from './formulas'
import { requestWallpapers, type RenderStage } from './renderClient'
import { renderScene } from './sceneRenderer'

function App() {
  const [config, setConfig] = useState<SceneConfig>(defaultSceneConfig)
  const [controlsPage, setControlsPage] = useState<'basic' | 'nerds'>('basic')
  const [isExporting, setIsExporting] = useState(false)
  const [renderStage, setRenderStage] = useState<RenderStage | null>(null)
  const [renderError, setRenderError] = useState<string | null>(null)
  const previewRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (previewRef.current) void renderScene(previewRef.current, config)
  }, [config])

  function update<K extends keyof SceneConfig>(key: K, value: SceneConfig[K]) {
    setConfig((current) => ({ ...current, [key]: value }))
  }

  async function downloadWallpapers() {
    setIsExporting(true)
    setRenderError(null)
    try {
      const urls = await requestWallpapers({ mass: 1, field_of_view: 20 }, setRenderStage)
      for (const url of urls) {
        const link = document.createElement('a')
        link.href = url
        link.download = ''
        link.click()
      }
    } catch (error) {
      setRenderError(error instanceof Error ? error.message : 'Could not create the server render.')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <main className={controlsPage === 'nerds' ? 'nerds-layout' : undefined}>
      <p className="eyebrow">Scientific cosmic generator</p>
      <h1>Gravitas</h1>
      <p className="tagline">Generative black-hole scenes, grounded in relativity.</p>
      <section className="studio">
        <div className="controls panel">
          <div className="tabs">
            <button type="button" className={controlsPage === 'basic' ? 'active' : ''} onClick={() => setControlsPage('basic')}>Scene</button>
            <button type="button" className={controlsPage === 'nerds' ? 'active' : ''} onClick={() => setControlsPage('nerds')}>For nerds</button>
          </div>
          <h2>{controlsPage === 'basic' ? 'Scene controls' : 'Model controls'}</h2>
          {controlsPage === 'basic' ? <>
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
            {isExporting ? `${renderStage ?? 'queued'} server render…` : 'Download both wallpapers'}
          </button>
          {renderError && <p role="alert">{renderError}</p>}
          </> : <>
          <p className="nerd-note">Fast-preview proxies. GR ray tracing will make these reference-quality.</p>
          <label>Inner disk radius <output>{config.innerDiskRadius} r₍g₎</output>
            <input type="range" min="1" max="20" value={config.innerDiskRadius} onChange={(event) => update('innerDiskRadius', Number(event.target.value))} />
          </label>
          <label>Emissivity slope <output>{config.emissivitySlope.toFixed(1)}</output>
            <input type="range" min="1" max="5" step="0.1" value={config.emissivitySlope} onChange={(event) => update('emissivitySlope', Number(event.target.value))} />
          </label>
          <label>Disk thickness H/R <output>{config.diskThickness.toFixed(2)}</output>
            <input type="range" min="0.02" max="0.5" step="0.01" value={config.diskThickness} onChange={(event) => update('diskThickness', Number(event.target.value))} />
          </label>
          <label>Flow direction
            <select value={config.flowDirection} onChange={(event) => update('flowDirection', event.target.value as SceneConfig['flowDirection'])}><option value="prograde">Prograde</option><option value="retrograde">Retrograde</option></select>
          </label>
          <label>Magnetic state
            <select value={config.magneticState} onChange={(event) => update('magneticState', event.target.value as SceneConfig['magneticState'])}><option value="sane">SANE</option><option value="mad">MAD</option></select>
          </label>
          <label>Jet strength <output>{config.jetStrength.toFixed(1)}</output>
            <input type="range" min="0" max="1" step="0.1" value={config.jetStrength} onChange={(event) => update('jetStrength', Number(event.target.value))} />
          </label>
          <label>Observing band
            <select value={config.observingBand} onChange={(event) => update('observingBand', event.target.value as SceneConfig['observingBand'])}><option value="230-ghz">230 GHz (EHT-like)</option><option value="optical">Optical visualization</option></select>
          </label>
          <p className="nerd-note">Magnetic state and observing band are saved with the scene but do not alter this fast preview yet.</p>
          </>}
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
        {controlsPage === 'nerds' && <aside className="formula-panel panel">
          <p className="eyebrow">Model notebook</p>
          <h2>What the controls mean</h2>
          <p className="nerd-note">Formulas guide the reference model. The fast preview uses labeled visual proxies.</p>
          {buildModelFormulas(config).map((formula) => <section key={formula.title}>
            <h3>{formula.title}</h3>
            <div className="equation" dangerouslySetInnerHTML={{ __html: katex.renderToString(formula.expression, { throwOnError: false }) }} />
            <p>{formula.note}</p>
          </section>)}
        </aside>}
      </section>
    </main>
  )
}

export default App
