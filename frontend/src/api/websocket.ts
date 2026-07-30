/** WebSocket connection manager for real-time game events. */
import type { GameState, TurnResult } from '../types';

export type WSMessageType =
  | 'game_state' | 'turn_result' | 'narration_chunk'
  | 'combat_started' | 'combat_update'
  | 'chat' | 'turn_update' | 'vision_update'
  | 'trade_offer' | 'trade_resolved'
  | 'item_used' | 'item_equipped' | 'item_unequipped'
  | 'player_joined' | 'player_left' | 'error' | 'reconnected';

export interface WSMessage {
  type: WSMessageType;
  payload: GameState | TurnResult | { player_id: string } | { message: string };
  /** Monotonic per-connection sequence stamped by useGameSocket so consumers
   * can process EVERY message, not just the newest one in a render batch. */
  seq?: number;
}

type MessageHandler = (message: WSMessage) => void;
type StatusHandler = (connected: boolean) => void;

export class GameWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private messageHandlers: MessageHandler[] = [];
  private statusHandlers: StatusHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectDelay = 15000;
  private reconnectDelay = 1000;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  private shouldReconnect = true;
  private hadConnection = false;
  // Liveness: any inbound frame proves the socket is alive. If nothing
  // arrives for > 2 heartbeat intervals (incl. pong replies), the socket is
  // presumed dead (phone slept, wifi switched) and force-closed to trigger
  // the reconnect path — browsers can keep zombie sockets "open" for minutes.
  private lastMessageAt = 0;
  private visibilityHandler: (() => void) | null = null;
  // Outbound messages queued while disconnected; flushed on (re)connect.
  private outbox: Record<string, unknown>[] = [];
  private maxOutbox = 50;

  constructor(sessionId: string, baseUrl?: string) {
    const wsBase = baseUrl || import.meta.env.VITE_WS_URL || `ws://${window.location.host}`;
    this.url = `${wsBase}/ws/game/${sessionId}`;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    // Phones fire visibilitychange when unlocked / switched back to the
    // browser — reconnect immediately instead of waiting out the backoff.
    if (!this.visibilityHandler && typeof document !== 'undefined') {
      this.visibilityHandler = () => {
        if (!document.hidden && this.shouldReconnect && !this.isConnected) {
          this.reconnectAttempts = 0;
          this.connect();
        }
      };
      document.addEventListener('visibilitychange', this.visibilityHandler);
    }

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      const isReconnect = this.hadConnection;
      this.hadConnection = true;
      this.reconnectAttempts = 0;
      this.lastMessageAt = Date.now();
      this.notifyStatus(true);
      this.startHeartbeat();
      // Deliver queued actions typed while offline, oldest first.
      const pending = this.outbox.splice(0, this.outbox.length);
      pending.forEach((msg) => this.send(msg));
      if (isReconnect) {
        // Let consumers re-join and re-fetch state after a drop.
        this.messageHandlers.forEach((handler) =>
          handler({ type: 'reconnected', payload: { message: 'reconnected' } }),
        );
      }
    };

    this.ws.onmessage = (event) => {
      this.lastMessageAt = Date.now();
      try {
        const raw = JSON.parse(event.data);
        // Backend sends flat messages; normalize to { type, payload } format
        const { type, ...rest } = raw;
        const message: WSMessage = { type, payload: raw.payload ?? rest };
        this.messageHandlers.forEach((handler) => handler(message));
      } catch {
        console.error('Failed to parse WebSocket message');
      }
    };

    this.ws.onclose = () => {
      this.notifyStatus(false);
      this.stopHeartbeat();
      if (this.shouldReconnect) {
        // Keep trying for the whole session — a table game runs for hours
        // and the backend may restart mid-session. Backoff caps at 15s.
        this.reconnectAttempts++;
        const delay = Math.min(
          this.reconnectDelay * this.reconnectAttempts,
          this.maxReconnectDelay,
        );
        setTimeout(() => this.connect(), delay);
      }
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.stopHeartbeat();
    if (this.visibilityHandler && typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', this.visibilityHandler);
      this.visibilityHandler = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  send(message: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else if (this.shouldReconnect && message.type !== 'ping') {
      // Queue non-heartbeat messages to deliver after reconnect.
      this.outbox.push(message);
      if (this.outbox.length > this.maxOutbox) this.outbox.shift();
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter((h) => h !== handler);
    };
  }

  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.push(handler);
    return () => {
      this.statusHandlers = this.statusHandlers.filter((h) => h !== handler);
    };
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private notifyStatus(connected: boolean): void {
    this.statusHandlers.forEach((handler) => handler(connected));
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      // Server answers every ping with a pong, so a healthy socket receives
      // at least one frame per interval. Silence for >2.5 intervals means
      // the connection is dead even if the browser still reports OPEN.
      if (this.lastMessageAt && Date.now() - this.lastMessageAt > 75000) {
        this.ws?.close(); // onclose schedules the reconnect
        return;
      }
      this.send({ type: 'ping' });
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}
