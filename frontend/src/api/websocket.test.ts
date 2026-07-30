/** GameWebSocket transport hardening — reconnect, liveness, outbox. */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { GameWebSocket } from './websocket';

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static OPEN = 1;
  static CLOSED = 3;
  readyState = 0;
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  url: string;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  simulateOpen() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  simulateMessage(obj: Record<string, unknown>) {
    this.onmessage?.({ data: JSON.stringify(obj) });
  }

  simulateClose() {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.();
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.simulateClose();
  }
}

describe('GameWebSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket as unknown as typeof WebSocket);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  function connect() {
    const gws = new GameWebSocket('sess-1', 'ws://test');
    gws.connect();
    const sock = FakeWebSocket.instances[0];
    return { gws, sock };
  }

  it('reconnects with backoff after the socket closes', () => {
    const { sock } = connect();
    sock.simulateOpen();
    sock.simulateClose();

    expect(FakeWebSocket.instances).toHaveLength(1);
    vi.advanceTimersByTime(1100); // first retry after ~1s
    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it('emits a reconnected event only on re-open, not first open', () => {
    const { gws, sock } = connect();
    const seen: string[] = [];
    gws.onMessage((m) => seen.push(m.type));

    sock.simulateOpen();
    expect(seen).not.toContain('reconnected');

    sock.simulateClose();
    vi.advanceTimersByTime(1100);
    FakeWebSocket.instances[1].simulateOpen();
    expect(seen).toContain('reconnected');
  });

  it('queues messages sent while disconnected and flushes on reconnect', () => {
    const { gws, sock } = connect();
    sock.simulateOpen();
    sock.simulateClose();

    gws.send({ type: 'action', action: 'I hide' });

    vi.advanceTimersByTime(1100);
    const sock2 = FakeWebSocket.instances[1];
    sock2.simulateOpen();

    const flushed = sock2.sent.map((s) => JSON.parse(s));
    expect(flushed.some((m) => m.type === 'action' && m.action === 'I hide')).toBe(true);
  });

  it('does not queue heartbeat pings while offline', () => {
    const { sock } = connect();
    sock.simulateOpen();
    sock.simulateClose();

    vi.advanceTimersByTime(1100);
    const sock2 = FakeWebSocket.instances[1];
    sock2.simulateOpen();
    const flushed = sock2.sent.map((s) => JSON.parse(s));
    expect(flushed.every((m) => m.type !== 'ping')).toBe(true);
  });

  it('force-closes a zombie socket that stops receiving frames', () => {
    const { sock } = connect();
    sock.simulateOpen();
    sock.simulateMessage({ type: 'pong' });

    // Silence across three heartbeat ticks (30s cadence): staleness passes
    // the 75s threshold on the third tick, which closes and reconnects.
    vi.advanceTimersByTime(95000);
    expect(sock.readyState).toBe(FakeWebSocket.CLOSED);
  });

  it('keeps a live socket open while frames keep arriving', () => {
    const { sock } = connect();
    sock.simulateOpen();

    for (let i = 0; i < 4; i++) {
      vi.advanceTimersByTime(25000);
      sock.simulateMessage({ type: 'pong' });
    }
    expect(sock.readyState).toBe(FakeWebSocket.OPEN);
  });

  it('reconnects immediately when the page becomes visible again', () => {
    const { sock } = connect();
    sock.simulateOpen();
    sock.simulateClose();

    // Before the backoff timer fires, the phone is unlocked:
    document.dispatchEvent(new Event('visibilitychange'));
    expect(FakeWebSocket.instances.length).toBeGreaterThanOrEqual(2);
  });

  it('stops reconnecting after an explicit disconnect', () => {
    const { gws, sock } = connect();
    sock.simulateOpen();
    gws.disconnect();

    vi.advanceTimersByTime(60000);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });
});
