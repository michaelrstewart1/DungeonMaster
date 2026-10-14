import { describe, expect, it } from 'vitest';
import { deliveryAfterServer, shownAsSent } from './actionDelivery';

describe('action delivery', () => {
  it('shows a line as sent only after the server accepts it', () => {
    expect(shownAsSent('pending')).toBe(false);
    expect(shownAsSent('failed')).toBe(false);
    expect(shownAsSent('sent')).toBe(true);
    expect(deliveryAfterServer('pending', 'ack')).toBe('sent');
    expect(deliveryAfterServer('pending', 'echo')).toBe('sent');
  });

  it('marks a line that never arrives as failed, and a late ack as sent', () => {
    expect(deliveryAfterServer('pending', 'timeout')).toBe('failed');
    expect(deliveryAfterServer('pending', 'error')).toBe('failed');
    expect(deliveryAfterServer('sent', 'error')).toBe('failed');
    expect(deliveryAfterServer('failed', 'ack')).toBe('sent');
    expect(deliveryAfterServer('sent', 'timeout')).toBe('sent');
  });
});
