import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'

const PRESETS = [
  { name: 'Auto', width: null, height: null },
  { name: 'Playing Card', width: 88, height: 63 },
  { name: 'Index Card', width: 127, height: 76 },
  { name: 'Badge', width: 85, height: 55 },
  { name: 'Bookmark', width: 150, height: 50 },
]

const PRINTERS = [
  { name: 'Bambu Lab A1 Mini', bedW: 180, bedH: 180 },
  { name: 'Bambu Lab A1', bedW: 256, bedH: 256 },
  { name: 'Bambu Lab P1S / X1C', bedW: 256, bedH: 256 },
  { name: 'Ender 3 / Pro / V2', bedW: 220, bedH: 220 },
  { name: 'Ender 3 S1', bedW: 220, bedH: 220 },
  { name: 'Ender 5', bedW: 220, bedH: 220 },
  { name: 'Prusa MK3S+', bedW: 250, bedH: 210 },
  { name: 'Prusa Mini+', bedW: 180, bedH: 180 },
  { name: 'Anycubic Kobra 2', bedW: 220, bedH: 220 },
  { name: 'Elegoo Neptune 3', bedW: 220, bedH: 220 },
  { name: 'Artillery Sidewinder X2', bedW: 300, bedH: 300 },
]

function BedPreview({ stencilW, stencilH, bedW, bedH }) {
  const maxDisplay = 240
  const scale = Math.min(maxDisplay / bedW, maxDisplay / bedH)
  const dW = bedW * scale
  const dH = bedH * scale
  const sW = stencilW * scale
  const sH = stencilH * scale
  const fits = stencilW <= bedW && stencilH <= bedH

  return (
    <div className="bed-preview-wrap">
      <svg width={dW + 2} height={dH + 2} viewBox={`-1 -1 ${dW + 2} ${dH + 2}`}>
        {/* Bed */}
        <rect x="0" y="0" width={dW} height={dH}
          fill="#f0f0f0" stroke="#ccc" strokeWidth="1" rx="4" />
        {/* Grid lines */}
        {Array.from({ length: Math.floor(bedW / 50) }, (_, i) => (
          <line key={`v${i}`} x1={(i + 1) * 50 * scale} y1="0"
            x2={(i + 1) * 50 * scale} y2={dH} stroke="#e0e0e0" strokeWidth="0.5" />
        ))}
        {Array.from({ length: Math.floor(bedH / 50) }, (_, i) => (
          <line key={`h${i}`} x1="0" y1={(i + 1) * 50 * scale}
            x2={dW} y2={(i + 1) * 50 * scale} stroke="#e0e0e0" strokeWidth="0.5" />
        ))}
        {/* Stencil — centered on bed */}
        <rect
          x={Math.max(0, (dW - sW) / 2)} y={Math.max(0, (dH - sH) / 2)}
          width={Math.min(sW, dW)} height={Math.min(sH, dH)}
          fill={fits ? 'rgba(74,108,247,0.25)' : 'rgba(220,38,38,0.2)'}
          stroke={fits ? '#4a6cf7' : '#dc2626'}
          strokeWidth="2" rx="2"
        />
        {/* Label on stencil */}
        <text
          x={dW / 2} y={dH / 2}
          textAnchor="middle" dominantBaseline="central"
          fontSize="11" fill={fits ? '#4a6cf7' : '#dc2626'} fontWeight="600"
        >
          {stencilW}x{stencilH}mm
        </text>
      </svg>
      <div className="bed-label">{bedW}x{bedH}mm bed</div>
    </div>
  )
}

function App() {
  const [text, setText] = useState('HELLO')
  const [width, setWidth] = useState(100)
  const [height, setHeight] = useState(50)
  const [thickness, setThickness] = useState(0.8)
  const [fontSize, setFontSize] = useState(40)
  const [margin, setMargin] = useState(10)
  const [hangingHole, setHangingHole] = useState(true)
  const [holeDiameter, setHoleDiameter] = useState(5)
  const [activePreset, setActivePreset] = useState('Auto')
  const [loading, setLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [error, setError] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [cornerRadius, setCornerRadius] = useState(3)
  const [unit, setUnit] = useState('mm')
  const [supportedChars, setSupportedChars] = useState(null)
  const [charWarning, setCharWarning] = useState(null)
  const [showBedCheck, setShowBedCheck] = useState(false)
  const [selectedPrinter, setSelectedPrinter] = useState(PRINTERS[0])

  const previewTimer = useRef(null)
  const autoSizeTimer = useRef(null)
  const undoStack = useRef([])
  const undoTimer = useRef(null)
  const isUndoing = useRef(false)

  // Undo: snapshot design state (debounced to batch rapid changes)
  const getSnapshot = useCallback(() => ({
    text, width, height, thickness, fontSize, margin,
    hangingHole, holeDiameter, activePreset, cornerRadius, unit
  }), [text, width, height, thickness, fontSize, margin,
       hangingHole, holeDiameter, activePreset, cornerRadius, unit])

  useEffect(() => {
    if (isUndoing.current) { isUndoing.current = false; return }
    if (undoTimer.current) clearTimeout(undoTimer.current)
    undoTimer.current = setTimeout(() => {
      const snap = getSnapshot()
      const stack = undoStack.current
      const last = stack[stack.length - 1]
      if (!last || JSON.stringify(last) !== JSON.stringify(snap)) {
        stack.push(snap)
        if (stack.length > 50) stack.shift()
      }
    }, 600)
    return () => clearTimeout(undoTimer.current)
  }, [getSnapshot])

  const undo = useCallback(() => {
    const stack = undoStack.current
    if (stack.length < 2) return
    stack.pop() // remove current state
    const prev = stack[stack.length - 1]
    isUndoing.current = true
    setText(prev.text)
    setWidth(prev.width)
    setHeight(prev.height)
    setThickness(prev.thickness)
    setFontSize(prev.fontSize)
    setMargin(prev.margin)
    setHangingHole(prev.hangingHole)
    setHoleDiameter(prev.holeDiameter)
    setActivePreset(prev.activePreset)
    setCornerRadius(prev.cornerRadius)
    setUnit(prev.unit)
  }, [])

  // Fetch supported characters on mount
  useEffect(() => {
    fetch(`${API_URL}/supported-characters`)
      .then(res => res.json())
      .then(data => setSupportedChars(new Set(data.characters.split(''))))
      .catch(() => {})
  }, [])

  // Filter text input to only supported characters
  const handleTextChange = (rawValue) => {
    const upper = rawValue.toUpperCase()
    if (!supportedChars) {
      setText(upper)
      setCharWarning(null)
      return
    }

    const filtered = []
    const rejected = new Set()
    for (const ch of upper) {
      if (supportedChars.has(ch) || supportedChars.has(ch.toLowerCase())) {
        filtered.push(ch)
      } else {
        rejected.add(ch)
      }
    }

    setText(filtered.join(''))

    if (rejected.size > 0) {
      const chars = [...rejected].map(c => `"${c}"`).join(', ')
      setCharWarning(`${chars} not available in stencil font`)
      setTimeout(() => setCharWarning(null), 3000)
    } else {
      setCharWarning(null)
    }
  }

  // Auto-size: when in Auto mode, compute plate size from text
  const autoSize = useCallback(async () => {
    if (activePreset !== 'Auto' || !text.trim()) return
    try {
      const res = await fetch(`${API_URL}/calculate-dimensions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim(), font_size: fontSize, margin }),
      })
      if (res.ok) {
        const data = await res.json()
        setWidth(Math.round(data.width))
        setHeight(Math.round(data.height))
      }
    } catch (err) {
      console.error('Auto-size error:', err)
    }
  }, [text, fontSize, margin, activePreset])

  // Fit text: when a preset size is selected, compute font size to fit
  const fitTextToPlate = useCallback(async (w, h) => {
    if (!text.trim()) return
    try {
      const res = await fetch(`${API_URL}/fit-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim(), width: w, height: h, margin }),
      })
      if (res.ok) {
        const data = await res.json()
        setFontSize(data.font_size)
      }
    } catch (err) {
      console.error('Fit text error:', err)
    }
  }, [text, margin])

  // When text or margin changes, re-fit or auto-size
  // NOTE: fontSize is intentionally excluded — we only auto-resize when
  // text/margin change, not when the user manually drags the font slider.
  useEffect(() => {
    if (activePreset === 'Auto') {
      if (autoSizeTimer.current) clearTimeout(autoSizeTimer.current)
      autoSizeTimer.current = setTimeout(autoSize, 300)
      return () => clearTimeout(autoSizeTimer.current)
    } else if (activePreset !== 'Custom') {
      // Fixed-size preset: re-fit font when text changes
      if (autoSizeTimer.current) clearTimeout(autoSizeTimer.current)
      autoSizeTimer.current = setTimeout(() => fitTextToPlate(width, height), 300)
      return () => clearTimeout(autoSizeTimer.current)
    }
  }, [text, margin, activePreset, autoSize, fitTextToPlate, width, height])

  // Initial auto-size on mount
  useEffect(() => {
    autoSize()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Ctrl+Z to undo
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
        // Don't intercept when typing in text input
        if (e.target.tagName === 'INPUT' && e.target.type === 'text') return
        e.preventDefault()
        undo()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [undo])

  // Debounced preview
  useEffect(() => {
    if (previewTimer.current) clearTimeout(previewTimer.current)
    previewTimer.current = setTimeout(async () => {
      if (!text.trim()) {
        setPreviewUrl(null)
        return
      }
      setPreviewLoading(true)
      try {
        const res = await fetch(`${API_URL}/preview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: text.trim(), width, height, thickness,
            font_size: fontSize, margin,
            hanging_hole: hangingHole, hole_diameter: holeDiameter,
            corner_radius: cornerRadius,
          }),
        })
        if (res.ok) {
          const blob = await res.blob()
          const url = URL.createObjectURL(blob)
          setPreviewUrl(prev => { if (prev) URL.revokeObjectURL(prev); return url })
          setError(null)
        } else {
          const err = await res.json().catch(() => ({}))
          setError(err.detail || 'Preview failed')
        }
      } catch {
        setError('Cannot reach server — is the backend running?')
      } finally {
        setPreviewLoading(false)
      }
    }, 400)
    return () => clearTimeout(previewTimer.current)
  }, [text, width, height, thickness, fontSize, margin, hangingHole, holeDiameter, cornerRadius])

  // Cleanup on unmount
  useEffect(() => {
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }
  }, [previewUrl])

  const applyPreset = (preset) => {
    setActivePreset(preset.name)
    if (preset.name === 'Auto') {
      autoSize()
    } else {
      setWidth(preset.width)
      setHeight(preset.height)
      fitTextToPlate(preset.width, preset.height)
    }
  }

  const doDownload = async () => {
    setShowBedCheck(false)
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/generate-stl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.trim(), width, height, thickness,
          font_size: fontSize, margin,
          hanging_hole: hangingHole, hole_diameter: holeDiameter,
          corner_radius: cornerRadius,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to generate STL')
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const safeName = text.trim().replace(/[^a-zA-Z0-9 _-]/g, '_') || 'stencil'
      a.download = `stencil_${safeName}.stl`
      document.body.appendChild(a)
      a.click()
      URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadSvg = async () => {
    if (!text.trim()) { setError('Type some text first!'); return }
    setError(null)
    try {
      const res = await fetch(`${API_URL}/generate-svg`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.trim(), width, height, thickness,
          font_size: fontSize, margin,
          hanging_hole: hangingHole, hole_diameter: holeDiameter,
          corner_radius: cornerRadius,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to generate SVG')
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const safeName = text.trim().replace(/[^a-zA-Z0-9 _-]/g, '_') || 'stencil'
      a.download = `stencil_${safeName}.svg`
      document.body.appendChild(a)
      a.click()
      URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDownloadClick = () => {
    if (!text.trim()) { setError('Type some text first!'); return }
    setShowBedCheck(true)
  }

  const resetToDefaults = () => {
    setText('HELLO')
    setThickness(0.8)
    setFontSize(40)
    setMargin(10)
    setHangingHole(true)
    setHoleDiameter(5)
    setActivePreset('Auto')
    setCornerRadius(3)
    setUnit('mm')
    setShowAdvanced(false)
    setError(null)
    setCharWarning(null)
    setTimeout(autoSize, 100)
  }

  const fits = width <= selectedPrinter.bedW && height <= selectedPrinter.bedH

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <img src="/logo-white.png" alt="SprayForge" className="header-logo" />
          <div>
            <h1>SprayForge</h1>
            <p className="tagline">Type it. Print it. Spray it.</p>
          </div>
        </div>
      </header>

      <main className="main">
        {/* Preview */}
        <section className="preview-card">
          {previewLoading && <div className="preview-spinner">Updating...</div>}
          {previewUrl ? (
            <img src={previewUrl} alt="Stencil preview" className="preview-img" />
          ) : (
            <div className="preview-empty">
              {text.trim() ? 'Loading preview...' : 'Type something to get started'}
            </div>
          )}
        </section>

        {/* Size warning */}
        {(width > 200 || height > 200) && (
          <div className="size-warning">
            Your stencil ({width}x{height}mm) may be too large for most 3D printers. Common print beds are around 220x220mm.
          </div>
        )}

        {/* Controls */}
        <section className="controls">
          {/* Text input */}
          <div className="field">
            <label htmlFor="text">Your Text</label>
            <input
              id="text"
              type="text"
              value={text}
              onChange={(e) => handleTextChange(e.target.value)}
              placeholder="e.g. ALEX"
              maxLength={30}
              autoFocus
            />
            {charWarning && <div className="char-warning">{charWarning}</div>}
          </div>

          {/* Presets */}
          <div className="field">
            <label>Size</label>
            <div className="preset-row">
              {PRESETS.map(p => (
                <button
                  key={p.name}
                  className={`preset-btn ${activePreset === p.name ? 'active' : ''} ${!p.width ? 'preset-btn-single' : ''}`}
                  onClick={() => applyPreset(p)}
                >
                  {p.name}
                  {p.width && <span className="preset-dim">{p.width}x{p.height}mm</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Hanging Hole */}
          <div className="field">
            <div className="hole-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={hangingHole}
                  onChange={(e) => setHangingHole(e.target.checked)}
                />
                <span>Hanging hole</span>
              </label>
              {hangingHole && (
                <select
                  className="hole-select"
                  value={holeDiameter}
                  onChange={(e) => setHoleDiameter(Number(e.target.value))}
                >
                  <option value={3}>Small (3mm)</option>
                  <option value={4}>Medium (4mm)</option>
                  <option value={5}>Standard (5mm)</option>
                  <option value={6}>Large (6mm)</option>
                  <option value={8}>Extra Large (8mm)</option>
                </select>
              )}
            </div>
          </div>

          {/* Font Size */}
          <div className="field">
            <label>Font Size: {fontSize}pt</label>
            <div className="viz-row">
              <div className="viz-box">
                <span
                  className="viz-letter"
                  style={{ fontSize: `${10 + ((fontSize - 8) / (120 - 8)) * 18}px` }}
                >A</span>
              </div>
              <input
                type="range" min="8" max="120" step="1"
                value={fontSize}
                onChange={(e) => { setFontSize(Number(e.target.value)); setActivePreset('Custom') }}
              />
            </div>
            <div className="range-hints">
              <span>Small</span>
              <span>Large</span>
            </div>
          </div>

          {/* Margin */}
          <div className="field">
            <label>Border Margin: {margin}mm</label>
            <div className="viz-row">
              <div className="viz-box">
                <div
                  className="viz-margin-box"
                  style={{ borderWidth: `${2 + ((margin - 3) / (30 - 3)) * 10}px` }}
                />
              </div>
              <input
                type="range" min="3" max="30" step="1"
                value={margin}
                onChange={(e) => setMargin(Number(e.target.value))}
              />
            </div>
            <div className="range-hints">
              <span>Tight</span>
              <span>Wide</span>
            </div>
          </div>

          {/* Thickness */}
          <div className="field">
            <label>Thickness: {thickness}mm</label>
            <div className="viz-row">
              <div className="viz-box">
                <div
                  className="viz-thickness-bar"
                  style={{ height: `${4 + ((thickness - 0.4) / (3 - 0.4)) * 28}px` }}
                />
              </div>
              <input
                type="range" min="0.4" max="3" step="0.1"
                value={thickness}
                onChange={(e) => setThickness(Number(e.target.value))}
              />
            </div>
            <div className="range-hints">
              <span>Thin (flexible)</span>
              <span>Thick (rigid)</span>
            </div>
          </div>

          {/* Advanced toggle */}
          <button
            className="advanced-toggle"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? 'Hide' : 'Show'} advanced options
          </button>

          {showAdvanced && (
            <div className="advanced-section">
              <div className="field">
                <label>Corner Rounding: {cornerRadius}mm</label>
                <input
                  type="range" min="0" max="15" step="1"
                  value={cornerRadius}
                  onChange={(e) => setCornerRadius(Number(e.target.value))}
                />
                <div className="range-hints">
                  <span>Sharp</span>
                  <span>Round</span>
                </div>
              </div>
              <div className="field">
                <div className="unit-row">
                  <label>Units</label>
                  <div className="unit-toggle">
                    <button
                      className={`unit-btn ${unit === 'mm' ? 'active' : ''}`}
                      onClick={() => setUnit('mm')}
                    >mm</button>
                    <button
                      className={`unit-btn ${unit === 'inches' ? 'active' : ''}`}
                      onClick={() => setUnit('inches')}
                    >inches</button>
                  </div>
                </div>
              </div>
              <div className="field">
                <label>Width: {unit === 'inches' ? (width / 25.4).toFixed(2) + '"' : width + 'mm'}</label>
                <input
                  type="range" min="30" max="300" step="1"
                  value={width}
                  onChange={(e) => { setWidth(Number(e.target.value)); setActivePreset('Custom') }}
                />
              </div>
              <div className="field">
                <label>Height: {unit === 'inches' ? (height / 25.4).toFixed(2) + '"' : height + 'mm'}</label>
                <input
                  type="range" min="20" max="200" step="1"
                  value={height}
                  onChange={(e) => { setHeight(Number(e.target.value)); setActivePreset('Custom') }}
                />
              </div>
            </div>
          )}

          {/* Error */}
          {error && <div className="error-msg">{error}</div>}

          {/* Actions */}
          <div className="action-row">
            <button
              className="undo-btn"
              onClick={undo}
              disabled={undoStack.current.length < 2}
              title="Undo (Ctrl+Z)"
            >
              Undo
            </button>
            <button
              className="reset-btn"
              onClick={resetToDefaults}
            >
              Reset
            </button>
            <button
              className="download-btn"
              onClick={handleDownloadClick}
              disabled={loading || !text.trim()}
            >
              {loading ? 'Generating...' : 'Download STL'}
            </button>
          </div>

          <p className="hint">
            Open the .stl file in your slicer (Cura, PrusaSlicer) to 3D print.
            <br />
            <button className="svg-link" onClick={downloadSvg} disabled={!text.trim()}>
              Download as SVG
            </button>
            {' '}for laser cutters.
          </p>
        </section>
      </main>

      {/* Bed Check Modal */}
      {showBedCheck && (
        <div className="modal-overlay" onClick={() => setShowBedCheck(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Check Printer Fit</h2>
            <p className="modal-subtitle">Make sure your stencil fits on the print bed</p>

            <div className="modal-printer-select">
              <label>Your Printer</label>
              <select
                value={selectedPrinter.name}
                onChange={(e) => setSelectedPrinter(PRINTERS.find(p => p.name === e.target.value))}
              >
                {PRINTERS.map(p => (
                  <option key={p.name} value={p.name}>
                    {p.name} ({p.bedW}x{p.bedH}mm)
                  </option>
                ))}
              </select>
            </div>

            <BedPreview
              stencilW={width} stencilH={height}
              bedW={selectedPrinter.bedW} bedH={selectedPrinter.bedH}
            />

            <div className={`fit-badge ${fits ? 'fits' : 'no-fit'}`}>
              {fits ? 'Fits on bed!' : 'Too large for this bed'}
            </div>

            <div className="modal-actions">
              <button className="modal-cancel" onClick={() => setShowBedCheck(false)}>
                Go Back
              </button>
              <button className="modal-confirm" onClick={doDownload}>
                {fits ? 'Download STL' : 'Download Anyway'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
