import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listGameSessions, resumeGameSession } from '../api/client';
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
  const [resuming, setResuming] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listGameSessions(campaignId)
      .then(data => { if (!cancelled) setSessions(data); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [campaignId]);

  // Restore server-side room code mapping before entering, so players
  // can rejoin with the original code even after a backend restart.
  const handleResume = async (sessionId: string, target: 'game' | 'lobby') => {
    setResuming(sessionId);
    try {
      await resumeGameSession(sessionId);
    } catch {
      // Session state fetch happens in the target page; proceed regardless.
    }
    navigate(target === 'lobby' ? `/lobby/${sessionId}` : `/game/${sessionId}`);
  };

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
            onClick={() => handleResume(session.id, 'game')}
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
                {session.room_code && (
                  <span className="session-room-code" title="Join code">🔑 {session.room_code}</span>
                )}
              </div>
              {session.scene && (
                <p className="session-scene-preview">{session.scene}</p>
              )}
              {i === 0 && (
                <div className="session-resume-actions">
                  <button
                    className="btn-primary btn-resume"
                    data-testid="btn-continue-session"
                    disabled={resuming === session.id}
                    onClick={(e) => { e.stopPropagation(); handleResume(session.id, 'game'); }}
                  >
                    {resuming === session.id ? 'Resuming…' : '▶ Continue Adventure'}
                  </button>
                  <button
                    className="btn-secondary btn-resume-table"
                    data-testid="btn-resume-table"
                    disabled={resuming === session.id}
                    onClick={(e) => { e.stopPropagation(); handleResume(session.id, 'lobby'); }}
                  >
                    🖥️ Resume Multiplayer Table
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
