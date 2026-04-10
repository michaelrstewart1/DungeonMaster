import type { Campaign } from '../types'

interface CampaignListProps {
  campaigns: Campaign[]
  onSelect: (id: string) => void
  onCreate: () => void
}

export function CampaignList({ campaigns, onSelect, onCreate }: CampaignListProps) {
  return (
    <div className="campaign-list">
      <div className="campaign-list-header">
        <h2>Campaigns</h2>
        <button onClick={onCreate} className="btn-primary">
          New Campaign
        </button>
      </div>

      {campaigns.length === 0 ? (
        <p className="empty-state">No campaigns yet. Create one to get started!</p>
      ) : (
        <div className="campaign-cards">
          {campaigns.map((campaign) => (
            <div
              key={campaign.id}
              className="campaign-card"
              onClick={() => onSelect(campaign.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onSelect(campaign.id)}
            >
              <h3>{campaign.name}</h3>
              <p className="campaign-description">{campaign.description}</p>
              <span className="campaign-meta">
                {campaign.character_ids.length} players
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
