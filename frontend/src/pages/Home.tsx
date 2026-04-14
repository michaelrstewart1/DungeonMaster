import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { CampaignList } from '../components/CampaignList'
import { getCampaigns, createCampaign, deleteCampaign, randomizeCampaign } from '../api/client'
import { PREMADE_CAMPAIGNS } from '../data/premadeCampaigns'
import type { Campaign } from '../types'
import type { PremadeCampaign } from '../data/premadeCampaigns'

export function Home() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formName, setFormName] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [randomizing, setRandomizing] = useState(false)
  const [launchingCampaign, setLaunchingCampaign] = useState<string | null>(null)
  const navigate = useNavigate()

  // Escape key closes the form
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showForm) setShowForm(false)
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [showForm])

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

  const handleDelete = async (id: string) => {
    try {
      await deleteCampaign(id)
      await loadCampaigns()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete campaign')
    }
  }

  const handleRandomize = async () => {
    setRandomizing(true)
    setError(null)
    try {
      const campaign = await randomizeCampaign()
      navigate(`/campaign/${campaign.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to randomize campaign')
      setRandomizing(false)
    }
  }

  const handleLaunchPremade = async (premade: PremadeCampaign) => {
    setLaunchingCampaign(premade.id)
    setError(null)
    try {
      const campaign = await createCampaign({
        name: premade.name,
        description: premade.description,
        world_state: premade.world_state,
        dm_settings: premade.dm_settings,
      })
      navigate(`/campaign/${campaign.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to launch campaign')
      setLaunchingCampaign(null)
    }
  }

  if (loading) return (
    <div className="page-home">
      <header className="hero">
        <h1>⚔️ AI Dungeon Master</h1>
        <p className="subtitle">Your AI-powered D&amp;D 5e experience</p>
      </header>
      <div className="home-content">
        <div className="loading-spinner">
          <div className="loading-d20"></div>
          <span className="loading-text">Summoning campaigns…</span>
        </div>
        <div className="loading-skeleton-cards">
          <div className="skeleton skeleton-card"></div>
          <div className="skeleton skeleton-card"></div>
          <div className="skeleton skeleton-card"></div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="page-home">
      <header className="hero">
        <div className="hero-emblem">⚔️</div>
        <h1>AI Dungeon Master</h1>
        <p className="subtitle">Your AI-powered D&amp;D 5e experience</p>
        <p className="hero-tagline">Roll for initiative. The DM is ready.</p>
        {campaigns.length > 0 && (
          <div className="hero-stats">
            <span className="hero-stat">
              <strong>{campaigns.length}</strong> {campaigns.length === 1 ? 'Campaign' : 'Campaigns'}
            </span>
            <span className="hero-stat-sep">•</span>
            <span className="hero-stat">
              <strong>{campaigns.reduce((sum, c) => sum + c.character_ids.length, 0)}</strong> Heroes
            </span>
          </div>
        )}
      </header>

      <div className="home-content">
        {error && <p className="error-message">{error}</p>}

        <section className="featured-campaigns">
          <h2 className="featured-title">⚔️ Featured Campaigns</h2>
          <p className="featured-subtitle">Jump into a handcrafted adventure — ready to play</p>
          <div className="featured-grid">
            {PREMADE_CAMPAIGNS.map((c) => (
              <button
                key={c.id}
                className="featured-card"
                onClick={() => handleLaunchPremade(c)}
                disabled={launchingCampaign !== null}
                aria-label={`Launch ${c.name}`}
              >
                <div className="featured-card-art" style={{ backgroundImage: `url(${c.thumbnail})` }}>
                  <div className="featured-card-overlay" />
                </div>
                <div className="featured-card-body">
                  <div className="featured-card-header">
                    <span className="featured-card-icon">{c.icon}</span>
                    <h3 className="featured-card-name">{c.name}</h3>
                  </div>
                  <p className="featured-card-theme">{c.theme}</p>
                  <p className="featured-card-desc">{c.description.slice(0, 120)}…</p>
                  <div className="featured-card-meta">
                    <span className="featured-badge">{c.levelRange}</span>
                    <span className="featured-badge">{c.playerCount}</span>
                  </div>
                </div>
                {launchingCampaign === c.id && (
                  <div className="featured-card-loading">Launching…</div>
                )}
              </button>
            ))}
          </div>
        </section>

        {showForm && (
          <form onSubmit={handleCreate} className="campaign-form" aria-label="Create campaign" role="form">
            <h3>New Campaign</h3>
            <div className="form-group">
              <label htmlFor="campaign-name">Name</label>
              <input
                id="campaign-name"
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Enter a name for your adventure..."
                required
                maxLength={50}
                autoFocus
              />
              <span className={`form-hint ${formName.length > 40 ? 'warn' : ''}`}>
                {formName.length}/50
              </span>
            </div>
            <div className="form-group">
              <label htmlFor="campaign-description">Description</label>
              <textarea
                id="campaign-description"
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                placeholder="Describe the world and setting..."
                required
                rows={3}
                maxLength={200}
              />
              <span className={`form-hint ${formDescription.length > 180 ? 'warn' : ''}`}>
                {formDescription.length}/200
              </span>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={creating || formName.trim().length < 2}>
                {creating ? 'Creating...' : 'Create Campaign'}
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
          onDelete={handleDelete}
          onRandomize={handleRandomize}
          randomizing={randomizing}
          loading={loading}
        />
      </div>
    </div>
  )
}
