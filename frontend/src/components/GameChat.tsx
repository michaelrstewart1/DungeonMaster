import { useState, useRef, useEffect, useCallback, useMemo } from 'react'

export interface ChatMessage {
  role: 'dm' | 'player'
  text: string
  timestamp?: number
}

type GamePhase = 'exploration' | 'combat' | 'lobby' | 'rest' | 'shopping' | 'dialogue'

type ActionCategory = 'explore' | 'interact' | 'combat' | 'magic' | 'utility'

interface QuickAction {
  emoji: string
  label: string
  category: ActionCategory
}

const EXPLORATION_ACTIONS: QuickAction[] = [
  { emoji: '🔍', label: 'Look Around', category: 'explore' },
  { emoji: '🚪', label: 'Open Door', category: 'explore' },
  { emoji: '💬', label: 'Talk to NPC', category: 'interact' },
  { emoji: '🎒', label: 'Check Inventory', category: 'utility' },
  { emoji: '⚔️', label: 'Draw Weapon', category: 'combat' },
  { emoji: '🏕️', label: 'Set Up Camp', category: 'utility' },
]

const COMBAT_ACTIONS: QuickAction[] = [
  { emoji: '⚔️', label: 'Attack', category: 'combat' },
  { emoji: '🛡️', label: 'Defend', category: 'combat' },
  { emoji: '🔮', label: 'Cast Spell', category: 'magic' },
  { emoji: '🏃', label: 'Dodge', category: 'utility' },
  { emoji: '💊', label: 'Use Potion', category: 'utility' },
  { emoji: '🏳️', label: 'Retreat', category: 'utility' },
]

interface GameChatProps {
  messages: ChatMessage[]
  onSubmitAction: (action: string) => void
  disabled?: boolean
  isWaitingForDM?: boolean
  phase?: GamePhase
}

type MessageMood = 'danger' | 'magic' | 'nature' | 'social' | 'dark' | 'neutral'

const MOOD_PATTERNS: { mood: MessageMood; pattern: RegExp }[] = [
  { mood: 'danger', pattern: /\b(attack|combat|fight|sword|blade|slash|blood|wound|strike|battle|death|kill|damage|crit|hit)\b/i },
  { mood: 'magic', pattern: /\b(spell|magic|arcane|enchant|glow|shimmer|mystic|rune|ward|aura|conjure|channel)\b/i },
  { mood: 'nature', pattern: /\b(forest|tree|river|wind|rain|sun|moon|star|flower|meadow|beast|animal|bird)\b/i },
  { mood: 'social', pattern: /\b(tavern|inn|merchant|shopkeep|barkeep|friend|ally|welcome|greet|smile|laugh|cheer)\b/i },
  { mood: 'dark', pattern: /\b(dark|shadow|dungeon|cavern|cave|tomb|crypt|undead|skeleton|ghost|whisper|dread|creep)\b/i },
]

function detectMood(text: string): MessageMood {
  let best: MessageMood = 'neutral'
  let bestCount = 0
  for (const { mood, pattern } of MOOD_PATTERNS) {
    const matches = text.match(new RegExp(pattern, 'gi'))
    if (matches && matches.length > bestCount) {
      bestCount = matches.length
      best = mood
    }
  }
  return best
}

/** Simple markdown-like formatting for DM narration */
function formatInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  let remaining = text
  let key = 0

  while (remaining.length > 0) {
    // Match **bold**
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/)
    // Match *italic*
    const italicMatch = remaining.match(/\*(.+?)\*/)
    // Match "quoted speech"
    const quoteMatch = remaining.match(/"([^"]+)"/)

    // Find earliest match
    const matches = [
      boldMatch ? { idx: remaining.indexOf(boldMatch[0]), match: boldMatch, type: 'bold' as const } : null,
      italicMatch && (!boldMatch || remaining.indexOf(italicMatch[0]) < remaining.indexOf(boldMatch[0])) 
        ? { idx: remaining.indexOf(italicMatch[0]), match: italicMatch, type: 'italic' as const } : null,
      quoteMatch ? { idx: remaining.indexOf(quoteMatch[0]), match: quoteMatch, type: 'quote' as const } : null,
    ].filter(Boolean).sort((a, b) => a!.idx - b!.idx)

    const first = matches[0]
    if (!first) {
      parts.push(remaining)
      break
    }

    if (first.idx > 0) {
      parts.push(remaining.slice(0, first.idx))
    }

    if (first.type === 'bold') {
      parts.push(<strong key={key++}>{first.match![1]}</strong>)
    } else if (first.type === 'italic') {
      parts.push(<em key={key++}>{first.match![1]}</em>)
    } else {
      parts.push(<span key={key++} className="speech-quote">&ldquo;{first.match![1]}&rdquo;</span>)
    }

    remaining = remaining.slice(first.idx + first.match![0].length)
  }

  return parts
}

/** Split DM text into paragraphs and apply inline formatting */
function formatMessage(text: string): React.ReactNode[] {
  // Split on double newlines or single newlines
  const paragraphs = text.split(/\n{2,}|\n/).filter(p => p.trim())
  if (paragraphs.length <= 1) {
    return formatInline(text)
  }
  return paragraphs.map((p, i) => (
    <span key={i} className="dm-paragraph">{formatInline(p.trim())}</span>
  ))
}

/** Typewriter effect for DM narration — types text character by character */
function TypewriterText({ text, onComplete }: { text: string; onComplete?: () => void }) {
  const containerRef = useRef<HTMLSpanElement>(null)
  const cursorRef = useRef<HTMLSpanElement>(null)
  const [done, setDone] = useState(false)
  const charIndex = useRef(0)
  const timeoutId = useRef<ReturnType<typeof setTimeout> | null>(null)

  const skip = useCallback(() => {
    if (done) return
    if (timeoutId.current !== null) {
      clearTimeout(timeoutId.current)
      timeoutId.current = null
    }
    if (containerRef.current) {
      containerRef.current.textContent = text
    }
    if (cursorRef.current) {
      cursorRef.current.style.display = 'none'
    }
    setDone(true)
    onComplete?.()
  }, [done, text, onComplete])

  useEffect(() => {
    charIndex.current = 0
    setDone(false)
    if (containerRef.current) {
      containerRef.current.textContent = ''
    }
    if (cursorRef.current) {
      cursorRef.current.style.display = 'inline'
    }

    function typeNext() {
      if (charIndex.current >= text.length) {
        if (cursorRef.current) {
          cursorRef.current.style.display = 'none'
        }
        setDone(true)
        onComplete?.()
        return
      }

      const char = text[charIndex.current]
      if (containerRef.current) {
        containerRef.current.textContent = text.slice(0, charIndex.current + 1)
      }
      charIndex.current++

      // Scroll the message into view as it types
      cursorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })

      // Determine delay for next character
      let delay = 30
      if (char === '.' || char === '!' || char === '?') {
        delay = 200
      } else if (char === ',' || char === ';' || char === ':') {
        delay = 100
      } else if (char === '\n') {
        delay = 150
      }

      timeoutId.current = setTimeout(typeNext, delay)
    }

    timeoutId.current = setTimeout(typeNext, 30)

    return () => {
      if (timeoutId.current !== null) {
        clearTimeout(timeoutId.current)
      }
    }
    // Only re-run when text changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text])

  return (
    <span className="typewriter-message" onClick={skip}>
      <span ref={containerRef} />
      <span ref={cursorRef} className="typewriter-cursor">▌</span>
    </span>
  )
}

function getQuickActions(phase: GamePhase): QuickAction[] {
  if (phase === 'combat') return COMBAT_ACTIONS
  return EXPLORATION_ACTIONS
}

export function GameChat({ messages, onSubmitAction, disabled = false, isWaitingForDM = false, phase = 'exploration' }: GameChatProps) {
  const [input, setInput] = useState('')
  const [showScrollBtn, setShowScrollBtn] = useState(false)
  const [typedMessageCount, setTypedMessageCount] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const prevMessageCount = useRef(0)

  // Track how many DM messages have been fully typed out.
  // Messages at indices < typedMessageCount are "historical" and render instantly.
  const dmMessageIndices = useMemo(() => {
    const indices: number[] = []
    messages.forEach((msg, i) => {
      if (msg.role === 'dm') indices.push(i)
    })
    return indices
  }, [messages])

  // When a new DM message arrives, it's the one that gets the typewriter effect.
  // All prior DM messages are considered already typed.
  useEffect(() => {
    if (messages.length > prevMessageCount.current) {
      // Mark all DM messages except the very last one as typed
      const lastDmIdx = dmMessageIndices.length - 1
      if (lastDmIdx >= 0 && messages[dmMessageIndices[lastDmIdx]].role === 'dm') {
        setTypedMessageCount(lastDmIdx)
      }
    }
    prevMessageCount.current = messages.length
  }, [messages, dmMessageIndices])

  const handleTypewriterComplete = useCallback(() => {
    setTypedMessageCount(prev => prev + 1)
  }, [])

  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleScroll = useCallback(() => {
    const el = chatContainerRef.current
    if (!el) return
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
    setShowScrollBtn(!isNearBottom)
  }, [])

  const autoResize = useCallback(() => {
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isWaitingForDM) {
      onSubmitAction(input.trim())
      setInput('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="game-chat">
      <div className="chat-messages" ref={chatContainerRef} onScroll={handleScroll}>
        {messages.length <= 3 && (
          <div className={`chat-watermark${messages.length > 0 ? ' chat-watermark-fading' : ''}`}>
            <div className="watermark-icon">⚔</div>
            <div className="watermark-text">Your adventure awaits...</div>
            <div className="watermark-ornament">✦ ✦ ✦</div>
          </div>
        )}
        {messages.map((msg, i) => {
          // Determine if this DM message should use the typewriter effect
          const dmIndex = msg.role === 'dm' ? dmMessageIndices.indexOf(i) : -1
          const isLatestDm = dmIndex >= 0 && dmIndex >= typedMessageCount
          const isTyping = isLatestDm && dmIndex === dmMessageIndices.length - 1
          const isNewest = i === messages.length - 1
          const mood = msg.role === 'dm' ? detectMood(msg.text) : 'neutral'

          return (
          <div key={i} className={`chat-message message-${msg.role}${msg.role === 'dm' ? ` mood-${mood}` : ''}${isNewest ? ' message-latest' : ''}`}>
            <div className="message-header">
              <span className="message-role">{msg.role === 'dm' ? '🎲 DM' : '⚔️ You'}</span>
              {msg.timestamp && (
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>
            <div className="message-text">
              {msg.role === 'dm' && isTyping
                ? <TypewriterText text={msg.text} onComplete={handleTypewriterComplete} />
                : msg.role === 'dm'
                  ? formatMessage(msg.text)
                  : msg.text}
            </div>
          </div>
          )
        })}
        {isWaitingForDM && (
          <div className="chat-message message-dm typing-message">
            <span className="message-role">🎲 DM</span>
            <div className="typing-indicator">
              <span className="typing-quill">✦</span>
              <span className="typing-text">The DM ponders your fate</span>
              <span className="typing-dots"><span></span><span></span><span></span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {showScrollBtn && (
        <button className="scroll-to-bottom" onClick={scrollToBottom} title="Scroll to latest">
          ↓
        </button>
      )}

      <div className={`quick-actions ${isWaitingForDM ? 'waiting' : ''}`}>
        {getQuickActions(phase).map((action, index) => (
          <button
            key={action.label}
            type="button"
            className="quick-action-btn"
            data-category={action.category}
            style={{ animationDelay: `${index * 0.05}s` }}
            disabled={disabled || isWaitingForDM}
            onClick={() => onSubmitAction(`${action.emoji} ${action.label}`)}
          >
            <span className="quick-action-emoji">{action.emoji}</span>
            <span className="quick-action-label">{action.label}</span>
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="chat-input-wrapper">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); autoResize() }}
            onKeyDown={handleKeyDown}
            placeholder="What do you do? (Enter to send, Shift+Enter for new line)"
            disabled={disabled || isWaitingForDM}
            className="chat-input"
            rows={1}
            maxLength={500}
          />
          {input.length > 400 && (
            <span className={`chat-char-count ${input.length > 480 ? 'warn' : ''}`}>
              {input.length}/500
            </span>
          )}
        </div>
        <button type="submit" disabled={disabled || isWaitingForDM || !input.trim()} className="chat-submit">
          Send
        </button>
      </form>
    </div>
  )
}
