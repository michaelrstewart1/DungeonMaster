import { useState, useRef, useCallback } from 'react'
import type { Character } from '../types'

interface CharacterImportProps {
  onImport: (character: Character) => void
  onCancel: () => void
}

type ImportTab = 'file' | 'paste'

export function CharacterImport({ onImport, onCancel }: CharacterImportProps) {
  const [activeTab, setActiveTab] = useState<ImportTab>('file')
  const [jsonText, setJsonText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null)
  const [importing, setImporting] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const parseAndPreview = useCallback((raw: string) => {
    setError(null)
    setPreview(null)
    try {
      const parsed = JSON.parse(raw)
      // Detect format: r20Exporter has "attribs" array
      const isR20 = parsed.attribs && Array.isArray(parsed.attribs)
      const format = isR20 ? 'r20' : 'generic'

      if (isR20) {
        const attribs = parsed.attribs as { name: string; current: string }[]
        const getAttr = (name: string) => attribs.find((a) => a.name === name)?.current || ''
        const levelMatch = getAttr('base_level').match(/(\w+)\s+(\d+)/)
        setPreview({
          format,
          name: parsed.name || getAttr('character_name') || 'Unknown',
          race: getAttr('race') || 'Unknown',
          class_name: levelMatch?.[1] || 'Unknown',
          level: levelMatch?.[2] || '1',
          strength: getAttr('strength') || '10',
          dexterity: getAttr('dexterity') || '10',
          constitution: getAttr('constitution') || '10',
          intelligence: getAttr('intelligence') || '10',
          wisdom: getAttr('wisdom') || '10',
          charisma: getAttr('charisma') || '10',
          hp: getAttr('hp') || '10',
          ac: getAttr('ac') || '10',
          _raw: parsed,
        })
      } else {
        setPreview({
          format,
          name: parsed.name || 'Unknown',
          race: parsed.race || 'Unknown',
          class_name: parsed.class_name || 'Unknown',
          level: String(parsed.level || 1),
          strength: String(parsed.strength || 10),
          dexterity: String(parsed.dexterity || 10),
          constitution: String(parsed.constitution || 10),
          intelligence: String(parsed.intelligence || 10),
          wisdom: String(parsed.wisdom || 10),
          charisma: String(parsed.charisma || 10),
          hp: String(parsed.hp || 10),
          ac: String(parsed.ac || 10),
          _raw: parsed,
        })
      }
    } catch {
      setError('Invalid JSON. Please check the format and try again.')
    }
  }, [])

  const handleFileSelect = useCallback((file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      setJsonText(text)
      parseAndPreview(text)
    }
    reader.onerror = () => setError('Failed to read file')
    reader.readAsText(file)
  }, [parseAndPreview])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileSelect(file)
  }, [handleFileSelect])

  const handleImport = async () => {
    if (!preview) return
    setImporting(true)
    setError(null)
    try {
      const format = preview.format as string
      const data = format === 'r20' ? preview._raw : preview._raw
      const response = await fetch('/api/characters/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format, data }),
      })
      if (!response.ok) {
        const errText = await response.text()
        throw new Error(errText || 'Import failed')
      }
      const character = await response.json()
      onImport(character)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed')
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="character-import" data-testid="character-import">
      <h2>Import Character</h2>
      <p className="import-description">
        Import from Roll20 (r20Exporter JSON) or paste character JSON
      </p>

      <div className="import-tabs" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'file'}
          className={`import-tab ${activeTab === 'file' ? 'active' : ''}`}
          onClick={() => setActiveTab('file')}
        >
          📁 Upload File
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'paste'}
          className={`import-tab ${activeTab === 'paste' ? 'active' : ''}`}
          onClick={() => setActiveTab('paste')}
        >
          📋 Paste JSON
        </button>
      </div>

      {activeTab === 'file' && (
        <div
          className={`import-drop-zone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          data-testid="drop-zone"
        >
          <div className="drop-icon">📜</div>
          <div className="drop-text">Drop JSON file here or click to browse</div>
          <div className="drop-hint">Supports r20Exporter .json files</div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
            data-testid="file-input"
          />
        </div>
      )}

      {activeTab === 'paste' && (
        <textarea
          className="import-json-input"
          placeholder='Paste character JSON here...'
          value={jsonText}
          onChange={(e) => {
            setJsonText(e.target.value)
            if (e.target.value.trim()) {
              parseAndPreview(e.target.value)
            } else {
              setPreview(null)
              setError(null)
            }
          }}
          data-testid="json-input"
        />
      )}

      {error && <div className="import-error" data-testid="import-error">{error}</div>}

      {preview && !error && (
        <div className="import-preview" data-testid="import-preview">
          <h3>Character Preview</h3>
          <div className="import-preview-grid">
            <span className="preview-label">Name</span>
            <span className="preview-value">{String(preview.name)}</span>
            <span className="preview-label">Race</span>
            <span className="preview-value">{String(preview.race)}</span>
            <span className="preview-label">Class</span>
            <span className="preview-value">{String(preview.class_name)}</span>
            <span className="preview-label">Level</span>
            <span className="preview-value">{String(preview.level)}</span>
            <span className="preview-label">HP</span>
            <span className="preview-value">{String(preview.hp)}</span>
            <span className="preview-label">AC</span>
            <span className="preview-value">{String(preview.ac)}</span>
            <span className="preview-label">STR / DEX / CON</span>
            <span className="preview-value">
              {String(preview.strength)} / {String(preview.dexterity)} / {String(preview.constitution)}
            </span>
            <span className="preview-label">INT / WIS / CHA</span>
            <span className="preview-value">
              {String(preview.intelligence)} / {String(preview.wisdom)} / {String(preview.charisma)}
            </span>
            <span className="preview-label">Format</span>
            <span className="preview-value">{preview.format === 'r20' ? 'Roll20 (r20Exporter)' : 'Generic JSON'}</span>
          </div>
        </div>
      )}

      <div className="form-actions">
        <button
          className="btn-primary"
          onClick={handleImport}
          disabled={!preview || importing || !!error}
          data-testid="import-btn"
        >
          {importing ? 'Importing...' : 'Import Character'}
        </button>
        <button className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  )
}
