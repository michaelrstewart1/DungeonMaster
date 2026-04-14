import { useState, useEffect, useRef, useCallback } from 'react'

export type NPCType = 'merchant' | 'guard' | 'wizard' | 'innkeeper' | 'mysterious' | 'noble' | 'default'

export interface NPCDialogueProps {
  npcName: string
  npcType: NPCType
  dialogue: string
  isActive: boolean
  onClose: () => void
}

/** Parse a DM message for NPC dialogue: returns name, type, and quoted speech or null. */
export function parseNPCDialogue(text: string): { npcName: string; npcType: NPCType; dialogue: string } | null {
  // Extract quoted speech
  const quoteMatch = text.match(/"([^"]+)"/)
  if (!quoteMatch) return null

  const dialogue = quoteMatch[1]
  const lower = text.toLowerCase()

  // Try pattern: "text" says/replies/speaks the NAME
  let npcName = 'Unknown NPC'
  const afterQuote = text.slice(text.indexOf(quoteMatch[0]) + quoteMatch[0].length)
  const sayAfter = afterQuote.match(/\b(?:says?|speaks?|replies?|responds?|whispers?|shouts?|exclaims?|mutters?|growls?|announces?)\b\s+(?:the\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)/)
  if (sayAfter) {
    npcName = sayAfter[1].trim()
  } else {
    // Try pattern: NAME says/replies "text"
    const beforeQuote = text.slice(0, text.indexOf(quoteMatch[0]))
    const sayBefore = beforeQuote.match(/([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:says?|speaks?|replies?|responds?|whispers?|shouts?|exclaims?|mutters?|growls?|announces?)\s*[:,]?\s*$/)
    if (sayBefore) {
      npcName = sayBefore[1].trim()
    } else {
      // Try pattern: The NAME says/speaks
      const thePattern = beforeQuote.match(/[Tt]he\s+([A-Z]?[a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+(?:says?|speaks?|replies?|responds?|whispers?|shouts?)\s*[:,]?\s*$/)
      if (thePattern) {
        npcName = thePattern[1].trim()
        // Capitalize first letter
        npcName = npcName.charAt(0).toUpperCase() + npcName.slice(1)
      }
    }
  }

  // Detect NPC type from context words
  const npcType = detectNPCType(lower)

  return { npcName, npcType, dialogue }
}

function detectNPCType(lower: string): NPCType {
  if (/\b(?:merchant|shop|buy|sell|wares|vendor|trader|goods|price|coin)\b/.test(lower)) return 'merchant'
  if (/\b(?:guard|soldier|patrol|captain|watch|sentry|knight|warrior)\b/.test(lower)) return 'guard'
  if (/\b(?:wizard|mage|sorcerer|archmage|conjurer|enchanter|warlock|witch)\b/.test(lower)) return 'wizard'
  if (/\b(?:inn|tavern|bartender|barkeep|innkeeper|ale|brew|drink)\b/.test(lower)) return 'innkeeper'
  if (/\b(?:hooded|shadow|stranger|cloaked|mysterious|dark figure|whisper|enigma)\b/.test(lower)) return 'mysterious'
  if (/\b(?:lord|lady|king|queen|prince|princess|noble|duke|duchess|baron|countess|regent)\b/.test(lower)) return 'noble'
  return 'default'
}

/* ── CSS Portrait Components ── */

function MerchantPortrait() {
  return (
    <div className="npc-portrait npc-portrait-merchant">
      <div className="portrait-hat merchant-hat" />
      <div className="portrait-face merchant-face">
        <div className="portrait-eye left" />
        <div className="portrait-eye right" />
        <div className="portrait-smile" />
      </div>
      <div className="portrait-body merchant-body" />
    </div>
  )
}

function GuardPortrait() {
  return (
    <div className="npc-portrait npc-portrait-guard">
      <div className="portrait-hat guard-helmet" />
      <div className="portrait-face guard-face">
        <div className="portrait-eye left" />
        <div className="portrait-eye right" />
        <div className="portrait-mouth guard-mouth" />
      </div>
      <div className="portrait-body guard-body">
        <div className="guard-shield" />
      </div>
    </div>
  )
}

function WizardPortrait() {
  return (
    <div className="npc-portrait npc-portrait-wizard">
      <div className="portrait-hat wizard-hat">
        <div className="wizard-star" />
      </div>
      <div className="portrait-face wizard-face">
        <div className="portrait-eye left wizard-eye" />
        <div className="portrait-eye right wizard-eye" />
        <div className="wizard-beard" />
      </div>
      <div className="portrait-body wizard-body" />
    </div>
  )
}

function InnkeeperPortrait() {
  return (
    <div className="npc-portrait npc-portrait-innkeeper">
      <div className="portrait-face innkeeper-face">
        <div className="portrait-eye left" />
        <div className="portrait-eye right" />
        <div className="portrait-smile innkeeper-smile" />
      </div>
      <div className="portrait-body innkeeper-body">
        <div className="innkeeper-apron" />
      </div>
    </div>
  )
}

function MysteriousPortrait() {
  return (
    <div className="npc-portrait npc-portrait-mysterious">
      <div className="portrait-hat mysterious-hood" />
      <div className="portrait-face mysterious-face">
        <div className="portrait-eye left mysterious-eye" />
        <div className="portrait-eye right mysterious-eye" />
      </div>
      <div className="portrait-body mysterious-body" />
    </div>
  )
}

function NoblePortrait() {
  return (
    <div className="npc-portrait npc-portrait-noble">
      <div className="portrait-hat noble-crown" />
      <div className="portrait-face noble-face">
        <div className="portrait-eye left" />
        <div className="portrait-eye right" />
        <div className="portrait-mouth noble-mouth" />
      </div>
      <div className="portrait-body noble-body" />
    </div>
  )
}

function DefaultPortrait() {
  return (
    <div className="npc-portrait npc-portrait-default">
      <div className="portrait-face default-face">
        <div className="portrait-eye left" />
        <div className="portrait-eye right" />
        <div className="portrait-mouth" />
      </div>
      <div className="portrait-body default-body" />
    </div>
  )
}

const PORTRAIT_MAP: Record<NPCType, React.FC> = {
  merchant: MerchantPortrait,
  guard: GuardPortrait,
  wizard: WizardPortrait,
  innkeeper: InnkeeperPortrait,
  mysterious: MysteriousPortrait,
  noble: NoblePortrait,
  default: DefaultPortrait,
}

const NPC_EMOJI: Record<NPCType, string> = {
  merchant: '🏪',
  guard: '🛡️',
  wizard: '🧙',
  innkeeper: '🍺',
  mysterious: '🎭',
  noble: '👑',
  default: '💬',
}

export function NPCDialogue({ npcName, npcType, dialogue, isActive, onClose }: NPCDialogueProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(true)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const autoDismissRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const charIndexRef = useRef(0)

  // Typewriter effect
  useEffect(() => {
    if (!isActive) return
    setDisplayedText('')
    setIsTyping(true)
    charIndexRef.current = 0

    const typeChar = () => {
      if (charIndexRef.current < dialogue.length) {
        charIndexRef.current += 1
        setDisplayedText(dialogue.slice(0, charIndexRef.current))
        timerRef.current = setTimeout(typeChar, 30)
      } else {
        setIsTyping(false)
      }
    }
    timerRef.current = setTimeout(typeChar, 100)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [isActive, dialogue])

  // Auto-dismiss after 10 seconds
  useEffect(() => {
    if (!isActive) return
    autoDismissRef.current = setTimeout(onClose, 10000)
    return () => {
      if (autoDismissRef.current) clearTimeout(autoDismissRef.current)
    }
  }, [isActive, onClose])

  // Skip typewriter on click
  const handleClick = useCallback(() => {
    if (isTyping) {
      // Finish typewriter immediately
      if (timerRef.current) clearTimeout(timerRef.current)
      setDisplayedText(dialogue)
      setIsTyping(false)
    } else {
      onClose()
    }
  }, [isTyping, dialogue, onClose])

  // Escape key dismisses
  useEffect(() => {
    if (!isActive) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isActive, onClose])

  if (!isActive) return null

  const Portrait = PORTRAIT_MAP[npcType]

  return (
    <div className="npc-dialogue-overlay" onClick={handleClick} data-testid="npc-dialogue">
      <div className="npc-dialogue-panel" onClick={e => e.stopPropagation()}>
        <div className="npc-dialogue-portrait-area">
          <Portrait />
          <div className="npc-dialogue-nameplate">
            <span className="npc-emoji">{NPC_EMOJI[npcType]}</span>
            <span className="npc-name">{npcName}</span>
          </div>
        </div>
        <div className="npc-dialogue-text-area">
          <div className="npc-dialogue-text">
            &ldquo;{displayedText}{isTyping && <span className="typing-cursor">|</span>}&rdquo;
          </div>
          <div className="npc-dialogue-hint">
            {isTyping ? 'Click to skip' : 'Click to dismiss'}
          </div>
        </div>
        <button className="npc-dialogue-close" onClick={onClose} aria-label="Close dialogue">✕</button>
      </div>
    </div>
  )
}
