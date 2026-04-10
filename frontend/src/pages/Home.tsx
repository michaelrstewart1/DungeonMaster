import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { CampaignList } from '../components/CampaignList'
import { getCampaigns, createCampaign } from '../api/client'
import type { Campaign } from '../types'

export function Home() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formName, setFormName] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()

  const loadCampaigns = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCampaigns()
      setCampaigns(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load campaigns')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCampaigns()
  }, [loadCampaigns])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setError(null)
    try {
      await createCampaign({ name: formName, description: formDescription })
      setFormName('')
      setFormDescription('')
      setShowForm(false)
      await loadCampaigns()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create campaign')
    } finally {
      setCreating(false)
    }
  }

  if (loading) return <div className="page-home">Loading...</div>

  return (
    <div className="page-home">
      <header className="hero">
        <h1>🐉 AI Dungeon Master</h1>
        <p>Your AI-powered D&amp;D 5e experience</p>
      </header>

      {error && <p className="error-message">{error}</p>}

      <main>
        {showForm && (
          <form onSubmit={handleCreate} className="campaign-form" aria-label="Create campaign">
            <div className="form-group">
              <label htmlFor="campaign-name">Name</label>
              <input
                id="campaign-name"
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="campaign-description">Description</label>
              <input
                id="campaign-description"
                type="text"
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                required
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={creating}>
                {creating ? 'Creating...' : 'Create'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                Cancel
              </button>
            </div>
          </form>
        )}

        <CampaignList
          campaigns={campaigns}
          onSelect={(id) => navigate(`/campaign/${id}`)}
          onCreate={() => setShowForm(true)}
        />
      </main>
    </div>
  )
}
