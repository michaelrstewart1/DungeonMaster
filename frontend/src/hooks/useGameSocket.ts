/** React hook for real-time game WebSocket connection.
 * Wraps GameWebSocket with React lifecycle management.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { GameWebSocket, type WSMessage } from '../api/websocket';

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

export function useGameSocket(sessionId: string | undefined): UseGameSocketReturn {
  const wsRef = useRef<GameWebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [players, setPlayers] = useState<PlayerInfo[]>([]);
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [connectionCount, setConnectionCount] = useState(0);

  useEffect(() => {
    if (!sessionId) return;

    const ws = new GameWebSocket(sessionId);
    wsRef.current = ws;

    const unsubStatus = ws.onStatusChange((isConnected) => {
      setConnected(isConnected);
    });

    const unsubMessage = ws.onMessage((msg) => {
      setMessages((prev) => [...prev.slice(-200), msg]); // keep last 200

      if (msg.type === 'player_joined') {
        const p = msg.payload as { player_id: string; connection_count?: number; name?: string };
        setConnectionCount(p.connection_count ?? 0);
        setPlayers((prev) => {
          if (prev.find((x) => x.id === p.player_id)) return prev;
          return [...prev, { id: p.player_id, name: p.name || 'Adventurer', isReady: false }];
        });
      }

      if (msg.type === 'player_left') {
        const p = msg.payload as { player_id: string; connection_count?: number };
        setConnectionCount(p.connection_count ?? 0);
        setPlayers((prev) => prev.filter((x) => x.id !== p.player_id));
      }

      if (msg.type === 'player_update' as string) {
        const p = msg.payload as { player_id: string; name?: string; characterId?: string; isReady?: boolean };
        setPlayers((prev) =>
          prev.map((x) =>
            x.id === p.player_id
              ? { ...x, ...(p.name && { name: p.name }), ...(p.characterId !== undefined && { characterId: p.characterId }), ...(p.isReady !== undefined && { isReady: p.isReady }) }
              : x,
          ),
        );
      }
    });

    ws.connect();

    return () => {
      unsubStatus();
      unsubMessage();
      ws.disconnect();
      wsRef.current = null;
    };
  }, [sessionId]);

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
    send({ type: 'player_join', name, character_id: characterId });
  }, [send]);

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
