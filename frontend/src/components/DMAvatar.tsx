interface DMAvatarProps {
  expression: string
  isSpeaking: boolean
  mouthAmplitude?: number
  gaze?: string
}

export function DMAvatar({ expression, isSpeaking, mouthAmplitude = 0, gaze = 'center' }: DMAvatarProps) {
  const mouthHeight = isSpeaking ? Math.max(4, Math.round(mouthAmplitude * 30)) : 4

  return (
    <div className={`dm-avatar ${isSpeaking ? 'is-speaking' : 'idle'}`}>
      <div className={`avatar-face expression-${expression}`}>
        {/* Eyes */}
        <div className="avatar-eyes">
          <div className={`avatar-eye left gaze-${gaze}`} />
          <div className={`avatar-eye right gaze-${gaze}`} />
        </div>

        {/* Mouth */}
        <div
          className="avatar-mouth"
          style={{ height: `${mouthHeight}px` }}
        />
      </div>

      <div className="avatar-label">
        <span className="expression-text">{expression}</span>
      </div>
    </div>
  )
}
