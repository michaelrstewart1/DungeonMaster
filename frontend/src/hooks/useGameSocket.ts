/** React hook for real-time game WebSocket connection.
 * Wraps GameWebSocket with React lifecycle management.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { GameWebSocket, type WSMessage } from '../api/websocket';
import { loadIdentity } from '../utils/playerIdentity';

export interface PlayerInfo {
  id: string;
  name: string;
  characterId?: string;
  isReady: boolean;
}

export interface UseGameSocketReturn {
  connected: boolean;
  players: PlayerInfo[];
  messages: WSMessage[];
  connectionCount: number;
  send: (msg: Record<string, unknown>) => void;
  sendChat: (message: string, sender: string) => void;
  sendAction: (characterId: string, action: string) => void;
  sendTokenMove: (tokenId: string, x: number, y: number) => void;
  joinAsPlayer: (name: string, characterId?: string) => void;
  setReady: (ready: boolean) => void;
}

export function useGameSocket(
  sessionId: string | undefined,
  options?: { observer?: boolean },
): UseGameSocketReturn {
  const wsRef = useRef<GameWebSocket | null>(null);
  const seqRef = useRef(0);
  const observer = options?.observer ?? false;
  const [connected, setConnected] = useState(false);
  const [players, setPlayers] = useState<PlayerInfo[]>([]);
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [connectionCount, setConnectionCount] = useState(0);

  useEffect(() => {
    if (!sessionId) return;

    const ws = new GameWebSocket(sessionId, undefined, observer ? 'observer' : undefined);
    wsRef.current = ws;

    const unsubStatus = ws.onStatusChange((isConnected) => {
      setConnected(isConnected);
    });

    const unsubMessage = ws.onMessage((msg) => {
      // Stamp a monotonic seq so consumers can catch up on message BURSTS —
      // reading only messages[length-1] drops frames when the server sends
      // several messages back-to-back (e.g. combat_started + combat_update).
      const stamped: WSMessage = { ...msg, seq: ++seqRef.current };
      setMessages((prev) => [...prev.slice(-200), stamped]); // keep last 200

      if (msg.type === 'reconnected') {
        // Connection dropped and came back (wifi blip, backend restart):
        // automatically re-register this player so the server rebinds the
        // socket for private messages and roster state. Observers never
        // re-join — they must stay invisible to the game.
        const identity = observer || !sessionId ? null : loadIdentity(sessionId);
        if (identity) {
          ws.send({
            type: 'player_join',
            name: identity.playerName,
            character_id: identity.characterId,
            player_id: identity.playerId,
          });
        }
      }

      if (msg.type === 'player_joined') {
        const p = msg.payload as { player_id: string; connection_count?: number; name?: string };
        setConnectionCount(p.connection_count ?? 0);
        // Anonymous WS connects (host laptop, TV display, lobby watchers) also
        // emit player_joined — without a name they are spectators, not players,
        // so don't add phantom "Adventurer" rows to the roster.
        if (p.name) {
          setPlayers((prev) => {
            if (prev.find((x) => x.id === p.player_id)) return prev;
            return [...prev, { id: p.player_id, name: p.name!, isReady: false }];
          });
        }
      }

      if (msg.type === 'player_left') {
        const p = msg.payload as { player_id: string; connection_count?: number };
        setConnectionCount(p.connection_count ?? 0);
        setPlayers((prev) => prev.filter((x) => x.id !== p.player_id));
      }

      if (msg.type === 'player_update' as string) {
        const p = msg.payload as {
          player_id?: string;
          name?: string;
          characterId?: string;
          isReady?: boolean;
          players?: Array<{ id: string; name?: string; character_id?: string; is_ready?: boolean }>;
          connection_count?: number;
        };
        if (p.connection_count !== undefined) setConnectionCount(p.connection_count);
        if (Array.isArray(p.players)) {
          // Server sends the authoritative full roster (from player_join /
          // player_ready) — replace local state so late joiners and rejoins
          // are never dropped.
          setPlayers(
            p.players.map((sp) => ({
              id: sp.id,
              name: sp.name || 'Adventurer',
              characterId: sp.character_id ?? undefined,
              isReady: !!sp.is_ready,
            })),
          );
        } else if (p.player_id) {
          setPlayers((prev) =>
            prev.map((x) =>
              x.id === p.player_id
                ? { ...x, ...(p.name && { name: p.name }), ...(p.characterId !== undefined && { characterId: p.characterId }), ...(p.isReady !== undefined && { isReady: p.isReady }) }
                : x,
            ),
          );
        }
      }
    });

    ws.connect();

    return () => {
      unsubStatus();
      unsubMessage();
      ws.disconnect();
      wsRef.current = null;
    };
  }, [sessionId, observer]);

  const send = useCallback((msg: Record<string, unknown>) => {
    wsRef.current?.send(msg);
  }, []);

  const sendChat = useCallback((message: string, sender: string) => {
    send({ type: 'chat', message, sender });
  }, [send]);

  const sendAction = useCallback((characterId: string, action: string) => {
    send({ type: 'action', character_id: characterId, action });
  }, [send]);

  const sendTokenMove = useCallback((tokenId: string, x: number, y: number) => {
    send({ type: 'token_move', token_id: tokenId, x, y });
  }, [send]);

  const joinAsPlayer = useCallback((name: string, characterId?: string) => {
    // Pass the durable player_id (localStorage identity, with legacy
    // sessionStorage fallback) so the server reconciles this WS connection
    // with the existing player row instead of creating a duplicate.
    const playerId =
      (sessionId ? loadIdentity(sessionId)?.playerId : undefined) ||
      sessionStorage.getItem('playerId') ||
      undefined;
    send({ type: 'player_join', name, character_id: characterId, player_id: playerId });
  }, [send, sessionId]);

  const setReady = useCallback((ready: boolean) => {
    send({ type: 'player_ready', ready });
  }, [send]);

  return {
    connected,
    players,
    messages,
    connectionCount,
    send,
    sendChat,
    sendAction,
    sendTokenMove,
    joinAsPlayer,
    setReady,
  };
}
