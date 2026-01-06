import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [text, setText] = useState('ALEX')
  const [width, setWidth] = useState(100)
  const [height, setHeight] = useState(50)
  const [thickness, setThickness] = useState(0.8)
  const [fontSize, setFontSize] = useState(40)
  const [margin, setMargin] = useState(10)
  const [loading, setLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [error, setError] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const debounceTimer = useRef(null)

  // Debounced preview update
  useEffect(() => {
    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    // Set new timer
    debounceTimer.current = setTimeout(async () => {
      if (!text.trim()) {
        setPreviewUrl(null)
        return
      }

      setPreviewLoading(true)
      try {
        const response = await fetch(`${API_URL}/preview`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: text.trim(),
            width,
            height,
            thickness,
            font_size: fontSize,
            margin,
          }),
        })

        if (response.ok) {
          const blob = await response.blob()
          const url = window.URL.createObjectURL(blob)
          // Clean up old preview URL
          setPreviewUrl(prev => {
            if (prev) {
              window.URL.revokeObjectURL(prev)
            }
            return url
          })
        }
      } catch (err) {
        console.error('Error fetching preview:', err)
      } finally {
        setPreviewLoading(false)
      }
    }, 500) // 500ms debounce

    // Cleanup
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }
    }
  }, [text, width, height, fontSize, margin, thickness])

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        window.URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const handleGenerate = async () => {
    if (!text.trim()) {
      setError('Please enter some text')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/generate-stl`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text.trim(),
          width,
          height,
          thickness,
          font_size: fontSize,
          margin,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate STL')
      }

      // Get the blob and create download link
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `stencil_${text.trim()}.stl`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="container">
        <h1>3D Printable Stencil Generator</h1>
        <p className="subtitle">Generate STL files for spray painting stencils</p>

        {/* Preview Section */}
        <div className="preview-section">
          <h2>Preview</h2>
          {previewLoading ? (
            <div className="preview-loading">Generating preview...</div>
          ) : previewUrl ? (
            <div className="preview-container">
              <img src={previewUrl} alt="Stencil preview" className="preview-image" />
            </div>
          ) : (
            <div className="preview-placeholder">
              Enter text above to see preview
            </div>
          )}
        </div>

        <div className="form">
          <div className="form-group">
            <label htmlFor="text">Text</label>
            <input
              id="text"
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter text (e.g., ALEX)"
              maxLength={50}
            />
          </div>

          <div className="form-group">
            <label htmlFor="width">
              Width: {width} mm
            </label>
            <input
              id="width"
              type="range"
              min="50"
              max="200"
              step="1"
              value={width}
              onChange={(e) => setWidth(Number(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label htmlFor="height">
              Height: {height} mm
            </label>
            <input
              id="height"
              type="range"
              min="30"
              max="150"
              step="1"
              value={height}
              onChange={(e) => setHeight(Number(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label htmlFor="thickness">
              Thickness: {thickness} mm
            </label>
            <input
              id="thickness"
              type="range"
              min="0.5"
              max="3.0"
              step="0.1"
              value={thickness}
              onChange={(e) => setThickness(Number(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label htmlFor="fontSize">
              Font Size: {fontSize} pt
            </label>
            <input
              id="fontSize"
              type="range"
              min="20"
              max="80"
              step="1"
              value={fontSize}
              onChange={(e) => setFontSize(Number(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label htmlFor="margin">
              Margin: {margin} mm
            </label>
            <input
              id="margin"
              type="range"
              min="5"
              max="30"
              step="1"
              value={margin}
              onChange={(e) => setMargin(Number(e.target.value))}
            />
          </div>

          {error && (
            <div className="error">
              {error}
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading || !text.trim()}
            className="generate-button"
          >
            {loading ? 'Generating...' : 'Download STL'}
          </button>
        </div>

        <div className="info">
          <p>
            <strong>Note:</strong> This tool uses a stencil font to prevent the middle of letters 
            (like 'O', 'A', 'P') from falling out. The generated STL file can be 3D printed and 
            used for spray painting.
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
