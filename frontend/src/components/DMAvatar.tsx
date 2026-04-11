interface DMAvatarProps {
  expression: string
  isSpeaking: boolean
  mouthAmplitude?: number
  gaze?: string
}

export function DMAvatar({ expression, isSpeaking, mouthAmplitude = 0, gaze = 'center' }: DMAvatarProps) {
  const mouthHeight = isSpeaking ? Math.max(6, Math.round(mouthAmplitude * 30)) : 4

  return (
    <div className={`dm-avatar ${isSpeaking ? 'is-speaking' : 'idle'}`}>
      <div className="dm-avatar-frame">
        <div className={`avatar-face expression-${expression}`}>
          {/* Hood silhouette */}
          <div className="avatar-hood" />

          {/* Eyes */}
          <div className="avatar-eyes">
            <div className={`avatar-eye left gaze-${gaze}`}>
              <div className="eye-glow" />
            </div>
            <div className={`avatar-eye right gaze-${gaze}`}>
              <div className="eye-glow" />
            </div>
          </div>

          {/* Mouth */}
          <div
            className={`avatar-mouth ${isSpeaking ? 'speaking' : ''}`}
            style={{ height: `${mouthHeight}px` }}
          />
        </div>
      </div>

      <div className="avatar-label">
        <span className="dm-title">Dungeon Master</span>
        <span className={`dm-status ${isSpeaking ? 'speaking' : 'idle'}`}>
          {isSpeaking ? '🔊 Speaking...' : expression === 'neutral' ? '⏳ Waiting' : `✨ ${expression}`}
        </span>
      </div>
    </div>
  )
}
