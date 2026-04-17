/** PlayerConnect — QR code + room code display for the DM sidebar.
 * Lets players at the table scan to join via their phones.
 */
import { useState, useEffect } from 'react'
import { QRCodeSVG } from 'qrcode.react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

interface PlayerConnectProps {
  sessionId: string
  connectedCount: number
  partySize: number
}

export function PlayerConnect({ sessionId, connectedCount, partySize }: PlayerConnectProps) {
  const [roomCode, setRoomCode] = useState('')
  const [collapsed, setCollapsed] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!sessionId) return
    fetch(`${API_BASE}/game/sessions/${sessionId}/room-code`)
      .then((r) => r.json())
      .then((data) => setRoomCode(data.room_code || ''))
      .catch(() => setError(true))
  }, [sessionId])

  // Auto-collapse QR after players connect (but keep room code visible)
  useEffect(() => {
    if (connectedCount > 1 && !collapsed) {
      setCollapsed(true)
    }
  }, [connectedCount, collapsed])

  const joinUrl = `${window.location.origin}/join?code=${roomCode}`

  if (error || !roomCode) {
    return null
  }

  return (
    <div className="player-connect">
      <div className="player-connect-header" onClick={() => setCollapsed(v => !v)}>
        <span className="player-connect-title">📱 Players</span>
        <span className="player-connect-count">
          {connectedCount > 1 ? connectedCount - 1 : 0}/{partySize}
        </span>
        <span className={`player-connect-chevron ${collapsed ? '' : 'expanded'}`}>▸</span>
      </div>

      {/* Room code always visible */}
      <div className="player-connect-code">
        <span className="room-code-label">Code:</span>
        <span className="room-code-value">{roomCode}</span>
      </div>

      {/* QR code collapsible */}
      {!collapsed && (
        <div className="player-connect-qr">
          <QRCodeSVG
            value={joinUrl}
            size={140}
            level="H"
            bgColor="#1a1a2e"
            fgColor="#c9a84c"
            includeMargin
          />
          <span className="player-connect-qr-label">Scan to join</span>
        </div>
      )}
    </div>
  )
}
