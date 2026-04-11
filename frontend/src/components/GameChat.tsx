import { useState, useRef, useEffect, useCallback } from 'react'

export interface ChatMessage {
  role: 'dm' | 'player'
  text: string
  timestamp?: number
}

interface GameChatProps {
  messages: ChatMessage[]
  onSubmitAction: (action: string) => void
  disabled?: boolean
  isWaitingForDM?: boolean
}

/** Simple markdown-like formatting for DM narration */
function formatMessage(text: string): React.ReactNode[] {
  // Split by bold **text** and italic *text* patterns
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

    // Add text before match
    if (first.idx > 0) {
      parts.push(remaining.slice(0, first.idx))
    }

    // Add formatted element
    if (first.type === 'bold') {
      parts.push(<strong key={key++}>{first.match![1]}</strong>)
    } else if (first.type === 'italic') {
      parts.push(<em key={key++}>{first.match![1]}</em>)
    } else {
      parts.push(<span key={key++} className="speech-quote">"{first.match![1]}"</span>)
    }

    remaining = remaining.slice(first.idx + first.match![0].length)
  }

  return parts
}

export function GameChat({ messages, onSubmitAction, disabled = false, isWaitingForDM = false }: GameChatProps) {
  const [input, setInput] = useState('')
  const [showScrollBtn, setShowScrollBtn] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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
    if (input.trim()) {
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
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message message-${msg.role}`}>
            <div className="message-header">
              <span className="message-role">{msg.role === 'dm' ? '🎲 DM' : '⚔️ You'}</span>
              {msg.timestamp && (
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>
            <p className="message-text">{msg.role === 'dm' ? formatMessage(msg.text) : msg.text}</p>
          </div>
        ))}
        {isWaitingForDM && (
          <div className="chat-message message-dm typing-message">
            <span className="message-role">🎲 DM</span>
            <div className="typing-indicator">
              <span></span><span></span><span></span>
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

      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="chat-input-wrapper">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); autoResize() }}
            onKeyDown={handleKeyDown}
            placeholder="What do you do? (Enter to send, Shift+Enter for new line)"
            disabled={disabled}
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
        <button type="submit" disabled={disabled || !input.trim()} className="chat-submit">
          Send
        </button>
      </form>
    </div>
  )
}
