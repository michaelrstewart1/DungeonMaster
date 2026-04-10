import { useState, useRef, useEffect } from 'react'

export interface ChatMessage {
  role: 'dm' | 'player'
  text: string
}

interface GameChatProps {
  messages: ChatMessage[]
  onSubmitAction: (action: string) => void
  disabled?: boolean
}

export function GameChat({ messages, onSubmitAction, disabled = false }: GameChatProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onSubmitAction(input.trim())
      setInput('')
    }
  }

  return (
    <div className="game-chat">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message message-${msg.role}`}>
            <span className="message-role">{msg.role === 'dm' ? '🎲 DM' : '⚔️ You'}</span>
            <p className="message-text">{msg.text}</p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="What do you do?"
          disabled={disabled}
          className="chat-input"
        />
        <button type="submit" disabled={disabled || !input.trim()} className="chat-submit">
          Send
        </button>
      </form>
    </div>
  )
}
