import { forwardRef, useImperativeHandle, useRef, useState } from 'react';

export interface PhoneActionInputHandle {
  /** Append a finished voice transcript without interleaving it into keystrokes. */
  insertTranscript: (text: string) => void;
}

interface PhoneActionInputProps {
  disabled?: boolean;
  placeholder?: string;
  onSend: (text: string) => void;
  onChat: (text: string) => void;
}

/**
 * The phone action box is uncontrolled on purpose.
 * A controlled `value` is rewritten on every game-socket render, and on a
 * phone that rewrite drops, reorders, or submits whatever prefix has landed
 * in React state. The field the player sees is the value that gets sent,
 * and only Enter or the action button sends it.
 */
export const PhoneActionInput = forwardRef<PhoneActionInputHandle, PhoneActionInputProps>(
  function PhoneActionInput({ disabled = false, placeholder, onSend, onChat }, ref) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [hasText, setHasText] = useState(false);

    function read(): string {
      return inputRef.current?.value ?? '';
    }

    function publishPresence() {
      setHasText(read().trim().length > 0);
    }

    function clear() {
      if (inputRef.current) inputRef.current.value = '';
      setHasText(false);
    }

    useImperativeHandle(ref, () => ({
      insertTranscript(text: string) {
        const extra = text.trim();
        const el = inputRef.current;
        if (!el || !extra) return;
        const next = el.value.trim() ? `${el.value.trim()} ${extra}` : extra;
        el.value = next;
        setHasText(true);
      },
    }));

    function sendAction() {
      if (disabled) return;
      const msg = read().trim();
      if (!msg) return;
      onSend(msg);
      clear();
    }

    function sendChat() {
      const msg = read().trim();
      if (!msg) return;
      onChat(msg);
      clear();
    }

    return (
      <div className="pv-action-bar">
        <input
          ref={inputRef}
          type="text"
          className="pv-action-input"
          defaultValue=""
          onInput={publishPresence}
          onKeyDown={(e) => {
            if (e.key !== 'Enter') return;
            // An IME confirmation reports Enter (keyCode 229) while the
            // composition is still open. Sending then would submit a partial word.
            const native = e.nativeEvent;
            if (native.isComposing || native.keyCode === 229) return;
            e.preventDefault();
            sendAction();
          }}
          placeholder={placeholder}
          disabled={disabled}
          aria-label="What do you do?"
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="none"
          spellCheck={false}
          inputMode="text"
          enterKeyHint="send"
        />
        <button
          type="button"
          className="pv-action-btn"
          onClick={sendAction}
          disabled={!hasText || disabled}
        >
          ⚔️
        </button>
        <button type="button" className="pv-chat-btn" onClick={sendChat} disabled={!hasText}>
          💬
        </button>
      </div>
    );
  },
);
