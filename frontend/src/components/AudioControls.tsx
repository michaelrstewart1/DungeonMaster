interface AudioControlsProps {
  isMicOn: boolean
  isMuted: boolean
  onMicToggle: () => void
  onMuteToggle: () => void
}

export function AudioControls({ isMicOn, isMuted, onMicToggle, onMuteToggle }: AudioControlsProps) {
  return (
    <div className={`audio-controls ${isMuted ? 'is-muted' : ''}`}>
      <button
        onClick={onMicToggle}
        className={`audio-btn mic-btn ${isMicOn ? 'active' : ''}`}
        aria-label={isMicOn ? 'Turn mic off' : 'Turn mic on'}
      >
        {isMicOn ? '🎙️' : '🔇'}
      </button>

      {isMicOn && <span className="recording-indicator">● Recording</span>}

      <button
        onClick={onMuteToggle}
        className={`audio-btn mute-btn ${isMuted ? 'active' : ''}`}
        aria-label={isMuted ? 'Unmute speaker' : 'Mute speaker'}
      >
        {isMuted ? '🔈' : '🔊'}
      </button>
    </div>
  )
}
