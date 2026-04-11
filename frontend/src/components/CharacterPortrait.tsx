import type { CharacterClass, Race } from '../types'
import { CLASS_COLORS, RACE_SYMBOLS } from '../data/premadeCharacters'

interface CharacterPortraitProps {
  race: Race
  className: CharacterClass
  portrait?: string
  size?: 'sm' | 'md' | 'lg'
  selected?: boolean
}

function isImagePath(str: string): boolean {
  return str.startsWith('/') || str.startsWith('http') || str.startsWith('data:')
}

export function CharacterPortrait({
  race,
  className,
  portrait,
  size = 'md',
  selected = false,
}: CharacterPortraitProps) {
  const colors = CLASS_COLORS[className]
  const symbol = portrait || RACE_SYMBOLS[race]
  const hasImage = portrait && isImagePath(portrait)

  const sizeMap = { sm: 64, md: 96, lg: 128 }
  const px = sizeMap[size]
  const fontSize = { sm: '1.5rem', md: '2.2rem', lg: '3rem' }

  return (
    <div
      className={`character-portrait ${selected ? 'selected' : ''} ${hasImage ? 'has-image' : ''}`}
      data-testid="character-portrait"
      style={{
        width: px,
        height: px,
        background: hasImage
          ? 'transparent'
          : `radial-gradient(ellipse at 30% 20%, ${colors.secondary}33, ${colors.primary}88, #0a0a0f)`,
        borderColor: selected ? '#d4a846' : colors.primary,
        boxShadow: selected
          ? `0 0 20px ${colors.accent}66, inset 0 0 30px ${colors.primary}22`
          : `inset 0 0 30px ${colors.primary}22`,
      }}
    >
      {hasImage ? (
        <img
          src={portrait}
          alt={`${race} ${className} portrait`}
          className="portrait-image"
          style={{ width: px, height: px }}
        />
      ) : (
        <span className="portrait-symbol" style={{ fontSize: fontSize[size] }}>
          {symbol}
        </span>
      )}
      <div className="portrait-frame" />
    </div>
  )
}
