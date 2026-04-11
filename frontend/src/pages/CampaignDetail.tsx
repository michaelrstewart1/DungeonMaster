import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getCampaign, getCharacters, createCharacter, createGameSession, deleteCharacter } from '../api/client'
import { CharacterSheet } from '../components/CharacterSheet'
import { CharacterCreator } from '../components/CharacterCreator'
import { CharacterImport } from '../components/CharacterImport'
import { CharacterPicker } from '../components/CharacterPicker'
import type { Campaign, Character, CharacterCreate } from '../types'

type CharacterMode = 'none' | 'premade' | 'manual' | 'import'

export function CampaignDetail() {
  const { campaignId } = useParams<{ campaignId: string }>()
  const navigate = useNavigate()

  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [characterMode, setCharacterMode] = useState<CharacterMode>('none')
  const [startingGame, setStartingGame] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    if (!campaignId) return
    setLoading(true)
    setError(null)
    try {
      const [campaignData, characterData] = await Promise.all([
        getCampaign(campaignId),
        getCharacters(campaignId),
      ])
      setCampaign(campaignData)
      setCharacters(characterData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load campaign')
    } finally {
      setLoading(false)
    }
  }, [campaignId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCreateCharacter = async (data: CharacterCreate) => {
    if (!campaignId) return
    setError(null)
    try {
      await createCharacter({ ...data, campaign_id: campaignId })
      setCharacterMode('none')
      setSuccessMessage(`${data.name} has joined the party!`)
      setTimeout(() => setSuccessMessage(null), 4000)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create character')
    }
  }

  const handleImportCharacter = async (_character: Character) => {
    setCharacterMode('none')
    await loadData()
  }

  const handleStartGame = async () => {
    if (!campaignId) return
    setStartingGame(true)
    setError(null)
    try {
      const session = await createGameSession(campaignId)
      navigate(`/game/${session.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start game')
      setStartingGame(false)
    }
  }

  const handleRemoveCharacter = async (characterId: string) => {
    try {
      await deleteCharacter(characterId)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove character')
    }
  }

  if (loading) return (
    <div className="page-campaign-detail">
      <div className="loading-spinner">
        <div className="loading-d20"></div>
        <span className="loading-text">Preparing adventure…</span>
      </div>
    </div>
  )

  if (error && !campaign) {
    return (
      <div className="page-campaign-detail">
        <p className="error-message">{error}</p>
      </div>
    )
  }

  return (
    <div className="page-campaign-detail">
      <nav className="breadcrumb">
        <button className="breadcrumb-link" onClick={() => navigate('/')}>
          ← Campaigns
        </button>
        <span className="breadcrumb-sep">/</span>
        <span className="breadcrumb-current">{campaign?.name}</span>
      </nav>
      <header>
        <h1>{campaign?.name}</h1>
        <p>{campaign?.description}</p>
      </header>

      {error && <p className="error-message">{error}</p>}
      {successMessage && (
        <div className="success-banner" data-testid="success-banner">
          <span className="success-icon">✨</span>
          <span>{successMessage}</span>
        </div>
      )}

      <section className="campaign-characters">
        <div className="section-header">
          <h2>Characters</h2>
        </div>

        {characterMode === 'none' && (
          <div className="character-mode-chooser" data-testid="mode-chooser">
            <button
              className="mode-card mode-premade"
              onClick={() => setCharacterMode('premade')}
              data-testid="btn-premade"
            >
              <span className="mode-icon">⚔️</span>
              <span className="mode-title">Choose a Hero</span>
              <span className="mode-desc">Pick from pre-made characters with portraits and backstories</span>
            </button>
            <button
              className="mode-card mode-custom"
              onClick={() => setCharacterMode('manual')}
              data-testid="btn-manual"
            >
              <span className="mode-icon">🔨</span>
              <span className="mode-title">Create Custom</span>
              <span className="mode-desc">Build your own character from scratch</span>
            </button>
            <button
              className="mode-card mode-import"
              onClick={() => setCharacterMode('import')}
              data-testid="btn-import"
            >
              <span className="mode-icon">📜</span>
              <span className="mode-title">Import Character</span>
              <span className="mode-desc">Import from Roll20 or paste character JSON</span>
            </button>
          </div>
        )}

        {characterMode === 'premade' && (
          <CharacterPicker
            onSelect={handleCreateCharacter}
            onCancel={() => setCharacterMode('none')}
          />
        )}

        {characterMode === 'import' && (
          <CharacterImport
            onImport={handleImportCharacter}
            onCancel={() => setCharacterMode('none')}
          />
        )}

        {characterMode === 'manual' && (
          <CharacterCreator
            onCreate={handleCreateCharacter}
            onCancel={() => setCharacterMode('none')}
          />
        )}

        {characters.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">🧙‍♂️</span>
            <span className="empty-state-title">No Characters Yet</span>
            <span className="empty-state-message">
              Choose a hero, create a custom character, or import from Roll20 to begin your quest.
            </span>
          </div>
        ) : (
          <>
            <div className="party-roster-header">
              <h3>Your Party ({characters.length})</h3>
              {characterMode === 'none' && (
                <button className="btn-add-more" onClick={() => setCharacterMode('premade')}>
                  + Add Another
                </button>
              )}
            </div>
            <div className="character-list">
              {characters.map((char) => (
                <CharacterSheet key={char.id} character={char} onRemove={handleRemoveCharacter} />
              ))}
            </div>
          </>
        )}
      </section>

      <section className="campaign-actions">
        {characters.length === 0 && (
          <p className="campaign-warning">
            ⚠️ You haven't added any characters yet. Add at least one hero before beginning your adventure!
          </p>
        )}
        <button
          className="btn-primary btn-start-game"
          onClick={handleStartGame}
          disabled={startingGame || characters.length === 0}
        >
          {startingGame ? 'Starting...' : 'Begin Adventure'}
        </button>
      </section>
    </div>
  )
}
