/** WebSocket connection manager for real-time game events. */
import type { GameState, TurnResult } from '../types';

export type WSMessageType = 'game_state' | 'turn_result' | 'player_joined' | 'player_left' | 'error' | 'reconnected';

export interface WSMessage {
  type: WSMessageType;
  payload: GameState | TurnResult | { player_id: string } | { message: string };
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
  // Outbound messages queued while disconnected; flushed on (re)connect.
  private outbox: Record<string, unknown>[] = [];
  private maxOutbox = 50;

  constructor(sessionId: string, baseUrl?: string) {
    const wsBase = baseUrl || import.meta.env.VITE_WS_URL || `ws://${window.location.host}`;
    this.url = `${wsBase}/ws/game/${sessionId}`;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      const isReconnect = this.hadConnection;
      this.hadConnection = true;
      this.reconnectAttempts = 0;
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
