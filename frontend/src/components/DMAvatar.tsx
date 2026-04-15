interface DMAvatarProps {
  expression: string
  isSpeaking: boolean
  mouthAmplitude?: number
  gaze?: string
}

export function DMAvatar({ expression, isSpeaking, mouthAmplitude = 0, gaze = 'center' }: DMAvatarProps) {
  // Eye position shifts based on gaze direction
  const gazeOffset = gaze === 'left' ? -3 : gaze === 'right' ? 3 : 0

  // Speaking animation: mouth opens wider
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
            {/* Eye glow filter */}
            <filter id="eyeGlow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Outer aura glow */}
            <filter id="auraGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Radial gradient for the dark orb background */}
            <radialGradient id="orbBg" cx="50%" cy="45%" r="50%">
              <stop offset="0%" stopColor="#1a1520" />
              <stop offset="60%" stopColor="#0d0a12" />
              <stop offset="100%" stopColor="#06050a" />
            </radialGradient>

            {/* Hood gradient */}
            <radialGradient id="hoodGrad" cx="50%" cy="20%" r="60%">
              <stop offset="0%" stopColor="#0a0810" stopOpacity="0.95" />
              <stop offset="50%" stopColor="#0d0a14" stopOpacity="0.85" />
              <stop offset="100%" stopColor="transparent" stopOpacity="0" />
            </radialGradient>

            {/* Eye gradient — golden iris */}
            <radialGradient id="eyeLeft" cx="40%" cy="40%" r="50%">
              <stop offset="0%" stopColor="#fff8dc" />
              <stop offset="30%" stopColor="#f5e6a8" />
              <stop offset="60%" stopColor="#d4a846" />
              <stop offset="100%" stopColor="#9a7a32" />
            </radialGradient>
            <radialGradient id="eyeRight" cx="40%" cy="40%" r="50%">
              <stop offset="0%" stopColor="#fff8dc" />
              <stop offset="30%" stopColor="#f5e6a8" />
              <stop offset="60%" stopColor="#d4a846" />
              <stop offset="100%" stopColor="#9a7a32" />
            </radialGradient>

            {/* Rune circle mask */}
            <clipPath id="circleClip">
              <circle cx="80" cy="80" r="72" />
            </clipPath>
          </defs>

          {/* Outer decorative rune ring */}
          <circle cx="80" cy="80" r="76" fill="none" stroke="#d4a846" strokeWidth="0.5"
            strokeOpacity="0.15" strokeDasharray="3 5" className="rune-ring" />

          {/* Main orb border */}
          <circle cx="80" cy="80" r="72" fill="url(#orbBg)"
            stroke="#d4a846" strokeWidth="2" strokeOpacity="0.5" className="orb-border" />

          {/* Inner decorative ring */}
          <circle cx="80" cy="80" r="68" fill="none"
            stroke="#d4a846" strokeWidth="0.5" strokeOpacity="0.1" />

          {/* Content clipped to circle */}
          <g clipPath="url(#circleClip)">
            {/* Hood silhouette — pointed cowl shape */}
            <path
              d="M80 8 C55 8 25 35 18 65 C14 80 16 100 22 115 L25 120
                 C30 108 38 85 45 72 C52 60 62 48 80 42
                 C98 48 108 60 115 72 C122 85 130 108 135 120
                 L138 115 C144 100 146 80 142 65 C135 35 105 8 80 8Z"
              fill="#0a0810"
              opacity="0.9"
            />
            {/* Hood inner shadow for depth */}
            <path
              d="M80 18 C60 20 35 42 30 65 C27 78 30 95 35 108
                 C42 92 52 72 60 62 C68 52 74 46 80 44
                 C86 46 92 52 100 62 C108 72 118 92 125 108
                 C130 95 133 78 130 65 C125 42 100 20 80 18Z"
              fill="#12101a"
              opacity="0.7"
            />
            {/* Face shadow area inside hood */}
            <ellipse cx="80" cy="78" rx="32" ry="28" fill="#0d0b14" opacity="0.6" />

            {/* Left eye — almond shaped */}
            <g filter="url(#eyeGlow)" className="avatar-eye-group left">
              <ellipse
                cx={56 + gazeOffset} cy="72" rx="10" ry="5.5"
                fill="url(#eyeLeft)"
                className="avatar-eye-shape"
              />
              {/* Pupil */}
              <ellipse
                cx={56 + gazeOffset} cy="72" rx="3.5" ry="4.5"
                fill="#0a0a10"
              />
              {/* Specular highlight */}
              <ellipse cx={53 + gazeOffset} cy="70" rx="2" ry="1.2" fill="white" opacity="0.7" />
            </g>

            {/* Right eye — almond shaped */}
            <g filter="url(#eyeGlow)" className="avatar-eye-group right">
              <ellipse
                cx={104 + gazeOffset} cy="72" rx="10" ry="5.5"
                fill="url(#eyeRight)"
                className="avatar-eye-shape"
              />
              {/* Pupil */}
              <ellipse
                cx={104 + gazeOffset} cy="72" rx="3.5" ry="4.5"
                fill="#0a0a10"
              />
              {/* Specular highlight */}
              <ellipse cx={101 + gazeOffset} cy="70" rx="2" ry="1.2" fill="white" opacity="0.7" />
            </g>

            {/* Nose shadow hint */}
            <line x1="80" y1="76" x2="80" y2="85" stroke="#d4a846" strokeWidth="0.5" opacity="0.1" />

            {/* Mouth — subtle, only visible when speaking */}
            {mouthOpen > 0 && (
              <ellipse
                cx="80" cy="92" rx={6 + mouthOpen} ry={mouthOpen}
                fill="#0a0810"
                stroke="#d4a846"
                strokeWidth="0.5"
                strokeOpacity="0.3"
                className="avatar-mouth-shape"
              />
            )}

            {/* Chin shadow when idle — subtle expression line */}
            {mouthOpen === 0 && (
              <path
                d="M73 90 Q80 93 87 90"
                fill="none" stroke="#d4a846" strokeWidth="0.5" opacity="0.15"
              />
            )}
          </g>

          {/* Ambient particles — floating embers/sparks */}
          <circle cx="30" cy="40" r="1" fill="#d4a846" opacity="0.3" className="spark spark-1" />
          <circle cx="130" cy="50" r="0.8" fill="#d4a846" opacity="0.2" className="spark spark-2" />
          <circle cx="45" cy="130" r="0.6" fill="#d4a846" opacity="0.25" className="spark spark-3" />
          <circle cx="120" cy="125" r="0.7" fill="#d4a846" opacity="0.2" className="spark spark-4" />
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
