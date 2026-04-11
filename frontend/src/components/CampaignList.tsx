import { useState } from 'react'
import type { Campaign } from '../types'

interface CampaignListProps {
  campaigns: Campaign[]
  onSelect: (id: string) => void
  onCreate: () => void
  onDelete?: (id: string) => void
}

const CAMPAIGN_ICONS = ['🏰', '🐉', '⚔️', '🗺️', '🏔️', '🌋', '🏜️', '🌊']

export function CampaignList({ campaigns, onSelect, onCreate, onDelete }: CampaignListProps) {
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (confirmDelete === id) {
      onDelete?.(id)
      setConfirmDelete(null)
    } else {
      setConfirmDelete(id)
    }
  }

  return (
    <div className="campaign-list">
      <div className="campaign-list-header">
        <h2>Campaigns</h2>
        <button onClick={onCreate} className="btn-primary">
          New Campaign
        </button>
      </div>

      {campaigns.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon">🏰</span>
          <span className="empty-state-title">No Campaigns Yet</span>
          <span className="empty-state-message">
            Create your first campaign to begin your adventure into the realms of fantasy.
          </span>
        </div>
      ) : (
        <div className="campaign-cards stagger-children">
          {campaigns.map((campaign, idx) => (
            <div
              key={campaign.id}
              className="campaign-card animate-in"
              onClick={() => onSelect(campaign.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onSelect(campaign.id)}
            >
              <div className="campaign-card-icon">{CAMPAIGN_ICONS[idx % CAMPAIGN_ICONS.length]}</div>
              {onDelete && (
                <button
                  className={`campaign-delete-btn ${confirmDelete === campaign.id ? 'confirming' : ''}`}
                  onClick={(e) => handleDelete(e, campaign.id)}
                  title={confirmDelete === campaign.id ? 'Click again to confirm' : 'Delete campaign'}
                  aria-label="Delete campaign"
                >
                  {confirmDelete === campaign.id ? '✓' : '✕'}
                </button>
              )}
              <h3>{campaign.name}</h3>
              {campaign.description && (
                <p className="campaign-description" title={campaign.description}>
                  {campaign.description.length > 80 
                    ? campaign.description.slice(0, 80) + '…' 
                    : campaign.description}
                </p>
              )}
              <div className="campaign-card-footer">
                <span className="campaign-meta">
                  {campaign.character_ids.length} {campaign.character_ids.length === 1 ? 'player' : 'players'}
                </span>
                {campaign.character_ids.length > 0 && (
                  <div className="campaign-party-dots">
                    {campaign.character_ids.slice(0, 4).map((_, i) => (
                      <span key={i} className="party-dot" />
                    ))}
                    {campaign.character_ids.length > 4 && (
                      <span className="party-dot-more">+{campaign.character_ids.length - 4}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
