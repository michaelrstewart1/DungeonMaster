/** DM-side trade arbitration panel.
 *
 * Shows all pending trades for the session and lets the DM veto any of them.
 * Subscribes to WS `trade_offer_observed` and `trade_resolved` messages
 * provided externally (the host page already owns the WS connection).
 */
import { useEffect, useState, useCallback } from 'react';
import type { Trade } from '../api/client';
import { listTrades, vetoTrade } from '../api/client';
import { useToast } from './Toast';

interface TradeArbitrationPanelProps {
  sessionId: string;
  /** WS messages forwarded from the parent so we don't open a second socket. */
  pendingTradesFromWs: Record<string, Trade>;
  /** Called when a trade is removed via veto/resolve, so parent can update state. */
  onTradeResolved?: (tradeId: string) => void;
}

export function TradeArbitrationPanel({ sessionId, pendingTradesFromWs, onTradeResolved }: TradeArbitrationPanelProps) {
  const { addToast } = useToast();
  const [vetoing, setVetoing] = useState<string | null>(null);
  const [reason, setReason] = useState<Record<string, string>>({});
  const [bootstrapped, setBootstrapped] = useState<Record<string, Trade>>({});

  // Bootstrap with any pending trades that existed before the panel mounted.
  useEffect(() => {
    if (!sessionId) return;
    listTrades(sessionId, undefined, 'pending')
      .then(({ trades }) => {
        const m: Record<string, Trade> = {};
        for (const t of trades) m[t.id] = t;
        setBootstrapped(m);
      })
      .catch(() => undefined);
  }, [sessionId]);

  const trades = { ...bootstrapped, ...pendingTradesFromWs };
  const list = Object.values(trades).filter((t) => t.status === 'pending');

  const handleVeto = useCallback(async (tradeId: string) => {
    setVetoing(tradeId);
    try {
      await vetoTrade(sessionId, tradeId, reason[tradeId]?.trim() || undefined);
      addToast({ type: 'success', message: 'Trade vetoed.' });
      onTradeResolved?.(tradeId);
      setBootstrapped((prev) => {
        const next = { ...prev };
        delete next[tradeId];
        return next;
      });
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : 'Veto failed' });
    } finally {
      setVetoing(null);
    }
  }, [sessionId, reason, addToast, onTradeResolved]);

  if (list.length === 0) {
    return (
      <div className="trade-arb-panel">
        <h3>🤝 Trade arbitration</h3>
        <div className="trade-arb-empty">No active trades.</div>
      </div>
    );
  }

  return (
    <div className="trade-arb-panel">
      <h3>🤝 Trade arbitration <span className="trade-arb-count">{list.length}</span></h3>
      <ul className="trade-arb-list">
        {list.map((t) => (
          <li key={t.id} className="trade-arb-row">
            <div className="trade-arb-summary">
              <strong>{t.from_player_name}</strong>
              {' → '}
              <strong>{t.to_player_name}</strong>
              <div className="trade-arb-detail">
                Offers: {summarize(t.offered_items, t.offered_gold)}
                <br />
                Asks: {summarize(t.requested_items, t.requested_gold)}
                {t.note ? <em> — “{t.note}”</em> : null}
              </div>
            </div>
            <div className="trade-arb-controls">
              <input
                type="text"
                placeholder="Reason (optional)"
                value={reason[t.id] || ''}
                onChange={(e) => setReason((prev) => ({ ...prev, [t.id]: e.target.value }))}
                className="trade-arb-reason"
              />
              <button
                type="button"
                className="trade-arb-veto-btn"
                onClick={() => handleVeto(t.id)}
                disabled={vetoing === t.id}
              >
                {vetoing === t.id ? '…' : 'Veto'}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function summarize(items: Trade['offered_items'], gold: number): string {
  const parts: string[] = items.map((i) => `${i.name ?? i.item_id} ×${i.quantity}`);
  if (gold > 0) parts.push(`${gold} gp`);
  return parts.length === 0 ? '(nothing)' : parts.join(', ');
}
