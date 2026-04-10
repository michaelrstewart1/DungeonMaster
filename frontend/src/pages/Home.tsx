import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CampaignList } from '../components/CampaignList'
import type { Campaign } from '../types'

export function Home() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/campaigns')
      .then((r) => r.json())
      .then(setCampaigns)
      .catch(() => {})
  }, [])

  return (
    <div className="page-home">
      <header className="hero">
        <h1>🐉 AI Dungeon Master</h1>
        <p>Your AI-powered D&D 5e experience</p>
      </header>

      <main>
        <CampaignList
          campaigns={campaigns}
          onSelect={(id) => navigate(`/campaign/${id}`)}
          onCreate={() => navigate('/campaign/new')}
        />
      </main>
    </div>
  )
}
