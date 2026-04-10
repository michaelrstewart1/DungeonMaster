import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getCampaign, getCharacters, createCharacter, createGameSession } from '../api/client'
import { CharacterSheet } from '../components/CharacterSheet'
import { CharacterCreator } from '../components/CharacterCreator'
import type { Campaign, Character, CharacterCreate } from '../types'

export function CampaignDetail() {
  const { campaignId } = useParams<{ campaignId: string }>()
  const navigate = useNavigate()

  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreator, setShowCreator] = useState(false)
  const [startingGame, setStartingGame] = useState(false)

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
      await createCharacter({ ...data, campaign_id: campaignId } as CharacterCreate & { campaign_id: string })
      setShowCreator(false)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create character')
    }
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

  if (loading) return <div className="page-campaign-detail">Loading...</div>

  if (error && !campaign) {
    return (
      <div className="page-campaign-detail">
        <p className="error-message">{error}</p>
      </div>
    )
  }

  return (
    <div className="page-campaign-detail">
      <header>
        <h1>{campaign?.name}</h1>
        <p>{campaign?.description}</p>
      </header>

      {error && <p className="error-message">{error}</p>}

      <section className="campaign-characters">
        <div className="section-header">
          <h2>Characters</h2>
          <button className="btn-primary" onClick={() => setShowCreator(true)}>
            Add Character
          </button>
        </div>

        {showCreator && (
          <CharacterCreator
            onCreate={handleCreateCharacter}
            onCancel={() => setShowCreator(false)}
          />
        )}

        {characters.length === 0 ? (
          <p className="empty-state">No characters yet. Add one to get started!</p>
        ) : (
          <div className="character-list">
            {characters.map((char) => (
              <CharacterSheet key={char.id} character={char} />
            ))}
          </div>
        )}
      </section>

      <section className="campaign-actions">
        <button
          className="btn-primary btn-start-game"
          onClick={handleStartGame}
          disabled={startingGame}
        >
          {startingGame ? 'Starting...' : 'Start Game'}
        </button>
      </section>
    </div>
  )
}
