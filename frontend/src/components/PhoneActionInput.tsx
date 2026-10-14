import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react';

export interface PhoneActionInputHandle {
  /** Append a finished voice transcript without interleaving it into keystrokes. */
  insertTranscript: (text: string) => void;
}

export interface PhoneActionDraftRef {
  current: string;
}

interface PhoneActionInputProps {
  disabled?: boolean;
  placeholder?: string;
  /** Parent-owned draft so a remount or a wiped DOM node can restore in-progress text. */
  draftRef?: PhoneActionDraftRef;
  onSend: (text: string) => void;
  onChat: (text: string) => void;
}

/**
 * The phone action box is uncontrolled on purpose.
 * A controlled `value` is rewritten on every game-socket render, and on a
 * phone that rewrite drops, reorders, or submits whatever prefix has landed
 * in React state. The field the player sees is the value that gets sent.
 *
 * The sword button and Enter share one submit. A phone keyboard's Enter
 * often has an empty `code`, so the key itself is what matters. Android and
 * iOS IMEs fire a confirming Enter *after* compositionend, when
 * `isComposing` is already false. That key is ignored for one tick so it
 * cannot send a prefix and wipe the rest of the sentence.
 */
export const PhoneActionInput = forwardRef<PhoneActionInputHandle, PhoneActionInputProps>(
  function PhoneActionInput({ disabled = false, placeholder, draftRef, onSend, onChat }, ref) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [hasText, setHasText] = useState(false);
    const composingRef = useRef(false);
    const suppressEnterRef = useRef(false);
    const suppressTimerRef = useRef<number | null>(null);
    const placeholderRef = useRef(placeholder);
    const disabledRef = useRef(disabled);
    const onSendRef = useRef(onSend);
    const onChatRef = useRef(onChat);
    placeholderRef.current = placeholder;
    disabledRef.current = disabled;
    onSendRef.current = onSend;
    onChatRef.current = onChat;

    function read(): string {
      return inputRef.current?.value ?? '';
    }

    function remember(value: string) {
      if (draftRef) draftRef.current = value;
    }

    function publishPresence() {
      setHasText(read().trim().length > 0);
    }

    function applyFieldAttrs() {
      const el = inputRef.current;
      if (!el || composingRef.current) return;
      if (placeholderRef.current !== undefined) el.placeholder = placeholderRef.current;
      el.disabled = disabledRef.current;
    }

    function clear() {
      if (inputRef.current) inputRef.current.value = '';
      remember('');
      setHasText(false);
    }

    useLayoutEffect(() => {
      const el = inputRef.current;
      if (el && !composingRef.current && el.value === '' && draftRef?.current) {
        el.value = draftRef.current;
        const end = el.value.length;
        try {
          el.setSelectionRange(end, end);
        } catch {
          /* setSelectionRange is unsupported for some input types. */
        }
        setHasText(el.value.trim().length > 0);
      }
      applyFieldAttrs();
    });

    useEffect(() => () => {
      if (suppressTimerRef.current != null) window.clearTimeout(suppressTimerRef.current);
    }, []);

    useImperativeHandle(ref, () => ({
      insertTranscript(text: string) {
        const extra = text.trim();
        const el = inputRef.current;
        if (!el || !extra) return;
        const next = el.value.trim() ? `${el.value.trim()} ${extra}` : extra;
        el.value = next;
        remember(next);
        setHasText(true);
      },
    }));

    function submit(kind: 'action' | 'chat') {
      if (kind === 'action' && disabledRef.current) return;
      const msg = read().trim();
      if (!msg) return;
      if (kind === 'action') onSendRef.current(msg);
      else onChatRef.current(msg);
      clear();
    }

    function armSuppressEnter() {
      suppressEnterRef.current = true;
      if (suppressTimerRef.current != null) window.clearTimeout(suppressTimerRef.current);
      suppressTimerRef.current = window.setTimeout(() => {
        suppressEnterRef.current = false;
        suppressTimerRef.current = null;
        applyFieldAttrs();
      }, 0);
    }

    function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
      if (e.key !== 'Enter') return;
      const native = e.nativeEvent;
      const implicit =
        native.isComposing ||
        native.keyCode === 229 ||
        composingRef.current ||
        suppressEnterRef.current;
      // Leave the IME's confirming Enter alone so it can commit the word.
      if (implicit) return;
      e.preventDefault();
      submit('action');
    }

    return (
      <div className="pv-action-bar">
        <input
          ref={inputRef}
          type="text"
          className="pv-action-input"
          defaultValue=""
          onInput={(e) => {
            remember(e.currentTarget.value);
            publishPresence();
          }}
          onCompositionStart={() => {
            composingRef.current = true;
          }}
          onCompositionEnd={() => {
            composingRef.current = false;
            remember(read());
            publishPresence();
            armSuppressEnter();
          }}
          onKeyDown={onKeyDown}
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
          onClick={() => submit('action')}
          disabled={!hasText || disabled}
          aria-label="Send action"
        >
          ⚔️
        </button>
        <button
          type="button"
          className="pv-chat-btn"
          onClick={() => submit('chat')}
          disabled={!hasText}
          aria-label="Send chat"
        >
          💬
        </button>
      </div>
    );
  },
);
