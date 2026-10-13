import { useState } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PhoneActionInput } from './PhoneActionInput';

const FULL = 'Kael shoots the leader from the door, no traps.';

function RerenderingBox({
  onSend,
  onChat,
}: {
  onSend: (text: string) => void;
  onChat: (text: string) => void;
}) {
  const [tick, setTick] = useState(0);
  return (
    <>
      <button type="button" onClick={() => setTick((n) => n + 1)}>
        socket {tick}
      </button>
      <PhoneActionInput
        placeholder={tick % 2 === 0 ? 'What do you do?' : 'Your turn'}
        onSend={onSend}
        onChat={onChat}
      />
    </>
  );
}

describe('PhoneActionInput', () => {
  it('keeps every typed character through socket rerenders and sends that exact text', async () => {
    const user = userEvent.setup({ delay: null });
    const onSend = vi.fn();
    const onChat = vi.fn();
    render(<RerenderingBox onSend={onSend} onChat={onChat} />);
    const input = screen.getByRole('textbox', { name: 'What do you do?' }) as HTMLInputElement;

    for (const chunk of ['Kael s', 'hoots the leader ', 'from the door, no traps.']) {
      await user.type(input, chunk);
      fireEvent.click(screen.getByRole('button', { name: /socket/ }));
      expect(onSend).not.toHaveBeenCalled();
      expect(onChat).not.toHaveBeenCalled();
    }

    expect(input.value).toBe(FULL);
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(onSend).toHaveBeenCalledTimes(1);
    expect(onSend).toHaveBeenCalledWith(FULL);
    expect(input.value).toBe('');
  });

  it('sends the text in the field, not a stale prefix from an earlier render', () => {
    const onSend = vi.fn();
    render(<PhoneActionInput onSend={onSend} onChat={vi.fn()} />);
    const input = screen.getByRole('textbox', { name: 'What do you do?' }) as HTMLInputElement;

    fireEvent.change(input, { target: { value: 'Kael s' } });
    input.value = FULL;
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(onSend).toHaveBeenCalledTimes(1);
    expect(onSend).toHaveBeenCalledWith(FULL);
  });

  it('does not submit while an IME composition is still confirming Enter', () => {
    const onSend = vi.fn();
    render(<PhoneActionInput onSend={onSend} onChat={vi.fn()} />);
    const input = screen.getByRole('textbox', { name: 'What do you do?' });
    fireEvent.change(input, { target: { value: FULL } });
    fireEvent.keyDown(input, { key: 'Enter', keyCode: 229, isComposing: true });
    expect(onSend).not.toHaveBeenCalled();
    expect((input as HTMLInputElement).value).toBe(FULL);
  });
});
