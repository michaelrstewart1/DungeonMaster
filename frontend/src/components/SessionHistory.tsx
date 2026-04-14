import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listGameSessions } from '../api/client';
import type { SessionSummary } from '../api/client';

interface SessionHistoryProps {
  campaignId: string;
}

function timeAgo(dateStr: string): string {
  if (!dateStr) return 'Unknown';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const PHASE_ICONS: Record<string, string> = {
  exploration: '🗺️',
  combat: '⚔️',
  social: '🗣️',
  rest: '🏕️',
};

export function SessionHistory({ campaignId }: SessionHistoryProps) {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    listGameSessions(campaignId)
      .then(data => { if (!cancelled) setSessions(data); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [campaignId]);

  if (loading) return null;
  if (sessions.length === 0) return null;

  return (
    <div className="session-history">
      <h3 className="session-history-title">📖 Session History</h3>
      <div className="session-history-timeline">
        {sessions.map((session, i) => (
          <div
            key={session.id}
            className={`session-history-item ${i === 0 ? 'latest' : ''}`}
            onClick={() => navigate(`/game/${session.id}`)}
            role="button"
            tabIndex={0}
          >
            <div className="session-timeline-dot" />
            <div className="session-history-content">
              <div className="session-history-meta">
                <span className="session-phase-icon">{PHASE_ICONS[session.phase] || '🎭'}</span>
                <span className="session-phase">{session.phase}</span>
                <span className="session-turns">{session.turn_count} turns</span>
                <span className="session-time">{timeAgo(session.created_at)}</span>
              </div>
              {session.scene && (
                <p className="session-scene-preview">{session.scene}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
