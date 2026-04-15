interface DMAvatarProps {
  expression: string
  isSpeaking: boolean
  mouthAmplitude?: number
  gaze?: string
}

export function DMAvatar({ expression, isSpeaking, mouthAmplitude = 0, gaze = 'center' }: DMAvatarProps) {
  const gazeOffset = gaze === 'left' ? -4 : gaze === 'right' ? 4 : 0
  const mouthOpen = isSpeaking ? Math.max(2, Math.round(mouthAmplitude * 8)) : 0

  return (
    <div className={`dm-avatar ${isSpeaking ? 'is-speaking' : 'idle'} expression-${expression}`}>
      <div className="dm-avatar-frame">
        <svg
          viewBox="0 0 160 160"
          className="dm-avatar-svg"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Strong eye glow — triple blur merge for intensity */}
            <filter id="eyeGlow" x="-150%" y="-150%" width="400%" height="400%">
              <feGaussianBlur stdDeviation="6" result="blur1" />
              <feGaussianBlur stdDeviation="3" in="SourceGraphic" result="blur2" />
              <feMerge>
                <feMergeNode in="blur1" />
                <feMergeNode in="blur1" />
                <feMergeNode in="blur2" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Ambient face glow from eyes illuminating hood */}
            <filter id="faceGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="12" />
            </filter>

            <radialGradient id="orbBg" cx="50%" cy="45%" r="50%">
              <stop offset="0%" stopColor="#14111c" />
              <stop offset="60%" stopColor="#0a0810" />
              <stop offset="100%" stopColor="#050408" />
            </radialGradient>

            {/* Eye gradient — bright golden with hot center */}
            <radialGradient id="eyeGrad" cx="35%" cy="35%" r="55%">
              <stop offset="0%" stopColor="#fffbe6" />
              <stop offset="20%" stopColor="#f5e6a8" />
              <stop offset="50%" stopColor="#d4a846" />
              <stop offset="85%" stopColor="#9a7a32" />
              <stop offset="100%" stopColor="#6b5420" />
            </radialGradient>

            <clipPath id="circleClip">
              <circle cx="80" cy="80" r="72" />
            </clipPath>
          </defs>

          {/* Outer decorative rune ring */}
          <circle cx="80" cy="80" r="76" fill="none" stroke="#d4a846" strokeWidth="0.5"
            strokeOpacity="0.15" strokeDasharray="3 5" className="rune-ring" />

          {/* Main orb */}
          <circle cx="80" cy="80" r="72" fill="url(#orbBg)"
            stroke="#d4a846" strokeWidth="2.5" strokeOpacity="0.45" className="orb-border" />

          {/* Inner ring */}
          <circle cx="80" cy="80" r="68" fill="none"
            stroke="#d4a846" strokeWidth="0.5" strokeOpacity="0.08" />

          <g clipPath="url(#circleClip)">
            {/* Hood — bold pointed cowl */}
            <path
              d="M80 5 C50 5 18 35 12 68 C8 85 12 105 20 120 L28 130
                 C35 110 45 85 55 72 C62 62 70 52 80 48
                 C90 52 98 62 105 72 C115 85 125 110 132 130
                 L140 120 C148 105 152 85 148 68 C142 35 110 5 80 5Z"
              fill="#08060e"
              opacity="0.95"
            />
            {/* Hood inner layer */}
            <path
              d="M80 15 C56 18 30 42 25 68 C22 82 25 98 32 112
                 C40 95 50 75 62 65 C70 57 76 50 80 48
                 C84 50 90 57 98 65 C110 75 120 95 128 112
                 C135 98 138 82 135 68 C130 42 104 18 80 15Z"
              fill="#0e0c16"
              opacity="0.8"
            />

            {/* Ambient golden glow cast by eyes onto inner hood */}
            <ellipse cx="80" cy="75" rx="35" ry="20"
              fill="#d4a846" opacity="0.04" filter="url(#faceGlow)" />

            {/* Face shadow pocket */}
            <ellipse cx="80" cy="80" rx="36" ry="30" fill="#0a0812" opacity="0.5" />

            {/* === LEFT EYE === */}
            <g filter="url(#eyeGlow)" className="avatar-eye-group left">
              {/* Eye shape — large almond */}
              <ellipse
                cx={60 + gazeOffset} cy="75" rx="14" ry="7.5"
                fill="url(#eyeGrad)"
                className="avatar-eye-shape"
              />
              {/* Dark slit pupil */}
              <ellipse
                cx={60 + gazeOffset} cy="75" rx="3" ry="6.5"
                fill="#06050a"
              />
              {/* Bright specular */}
              <ellipse cx={55 + gazeOffset} cy="72.5" rx="3" ry="1.8"
                fill="white" opacity="0.8" />
              {/* Secondary highlight */}
              <ellipse cx={63 + gazeOffset} cy="77" rx="1.5" ry="1"
                fill="white" opacity="0.3" />
            </g>

            {/* === RIGHT EYE === */}
            <g filter="url(#eyeGlow)" className="avatar-eye-group right">
              <ellipse
                cx={100 + gazeOffset} cy="75" rx="14" ry="7.5"
                fill="url(#eyeGrad)"
                className="avatar-eye-shape"
              />
              <ellipse
                cx={100 + gazeOffset} cy="75" rx="3" ry="6.5"
                fill="#06050a"
              />
              <ellipse cx={95 + gazeOffset} cy="72.5" rx="3" ry="1.8"
                fill="white" opacity="0.8" />
              <ellipse cx={103 + gazeOffset} cy="77" rx="1.5" ry="1"
                fill="white" opacity="0.3" />
            </g>

            {/* Nose shadow hint */}
            <line x1="80" y1="82" x2="80" y2="90" stroke="#d4a846"
              strokeWidth="0.4" opacity="0.08" />

            {/* Mouth — visible when speaking */}
            {mouthOpen > 0 && (
              <ellipse
                cx="80" cy="96" rx={7 + mouthOpen} ry={mouthOpen}
                fill="#08060e"
                stroke="#d4a846" strokeWidth="0.5" strokeOpacity="0.25"
                className="avatar-mouth-shape"
              />
            )}

            {/* Idle expression line */}
            {mouthOpen === 0 && (
              <path
                d="M72 94 Q80 97 88 94"
                fill="none" stroke="#d4a846" strokeWidth="0.5" opacity="0.1"
              />
            )}
          </g>

          {/* Floating sparks */}
          <circle cx="28" cy="38" r="1.2" fill="#d4a846" opacity="0.3" className="spark spark-1" />
          <circle cx="135" cy="48" r="1" fill="#d4a846" opacity="0.25" className="spark spark-2" />
          <circle cx="40" cy="135" r="0.8" fill="#d4a846" opacity="0.2" className="spark spark-3" />
          <circle cx="125" cy="128" r="0.9" fill="#d4a846" opacity="0.22" className="spark spark-4" />
        </svg>
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
