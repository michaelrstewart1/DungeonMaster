/** Player-to-player trade UI.
 *
 * Two surfaces:
 *  - TradeOfferModal: shown to an initiating player to compose an offer.
 *  - IncomingTradeModal: shown to a recipient when they receive `trade_offer`
 *    over the WebSocket.
 *
 * Designed for mobile: full-width sheets, big tap targets, single-column layout.
 */
import { useEffect, useMemo, useState } from 'react';
import type { Character, StructuredItem } from '../types';
import type { Trade, TradeItemRef } from '../api/client';
import { createTrade, respondTrade, cancelTrade, counterTrade } from '../api/client';
import { useToast } from './Toast';

interface Player {
  id: string;
  name: string;
  characterId?: string;
}

interface TradeOfferModalProps {
  sessionId: string;
  fromPlayerId: string;
  fromCharacter: Character;
  candidates: Player[];
  initialTo?: Player;
  onClose: () => void;
  onSent?: (trade: Trade) => void;
}

export function TradeOfferModal({
  sessionId,
  fromPlayerId,
  fromCharacter,
  candidates,
  initialTo,
  onClose,
  onSent,
}: TradeOfferModalProps) {
  const { addToast } = useToast();
  const [to, setTo] = useState<Player | null>(initialTo ?? candidates[0] ?? null);
  const [selectedItems, setSelectedItems] = useState<Record<string, number>>({});
  const [offeredGold, setOfferedGold] = useState<number>(0);
  const [requestedGold, setRequestedGold] = useState<number>(0);
  const [note, setNote] = useState('');
  const [sending, setSending] = useState(false);

  const inventory: StructuredItem[] = useMemo(
    () => fromCharacter.structured_inventory ?? [],
    [fromCharacter.structured_inventory],
  );

  const toggleItem = (item: StructuredItem) => {
    setSelectedItems((prev) => {
      const next = { ...prev };
      if (next[item.id]) {
        delete next[item.id];
      } else {
        next[item.id] = 1;
      }
      return next;
    });
  };

  const setQty = (item: StructuredItem, qty: number) => {
    const clamped = Math.max(1, Math.min(item.quantity, qty));
    setSelectedItems((prev) => ({ ...prev, [item.id]: clamped }));
  };

  const handleSend = async () => {
    if (!to) {
      addToast({ type: 'error', message: 'Pick a recipient first.' });
      return;
    }
    const items: TradeItemRef[] = Object.entries(selectedItems).map(([id, qty]) => ({ item_id: id, quantity: qty }));
    if (items.length === 0 && offeredGold === 0 && requestedGold === 0) {
      addToast({ type: 'error', message: 'Offer at least one item or some gold.' });
      return;
    }
    setSending(true);
    try {
      const res = await createTrade(sessionId, {
        from_player_id: fromPlayerId,
        from_character_id: fromCharacter.id,
        to_player_id: to.id,
        to_character_id: to.characterId,
        offered_items: items,
        offered_gold: offeredGold,
        requested_gold: requestedGold,
        note,
      });
      addToast({
        type: 'success',
        title: 'Trade sent',
        message: res.delivered ? `${to.name} was notified.` : `${to.name} is offline; they'll see it on reconnect.`,
      });
      onSent?.(res.trade);
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Trade failed';
      addToast({ type: 'error', title: 'Could not send trade', message: msg });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="trade-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="trade-modal" onClick={(e) => e.stopPropagation()}>
        <header className="trade-modal-header">
          <h2>🤝 Offer a trade</h2>
          <button className="trade-modal-close" onClick={onClose} aria-label="Close">×</button>
        </header>

        <div className="trade-modal-body">
          <label className="trade-field">
            <span>Send to</span>
            <select
              className="trade-select"
              value={to?.id || ''}
              onChange={(e) => setTo(candidates.find((p) => p.id === e.target.value) ?? null)}
            >
              {candidates.length === 0 ? <option value="">(no other players)</option> : null}
              {candidates.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </label>

          <div className="trade-section">
            <div className="trade-section-title">Your items</div>
            {inventory.length === 0 ? (
              <div className="trade-empty">No tradeable items yet. Ask the DM to distribute loot.</div>
            ) : (
              <ul className="trade-items">
                {inventory.map((item) => {
                  const picked = item.id in selectedItems;
                  return (
                    <li key={item.id} className={`trade-item ${picked ? 'is-picked' : ''}`}>
                      <button className="trade-item-row" onClick={() => toggleItem(item)} aria-pressed={picked}>
                        <span className="trade-item-name">{item.name}</span>
                        <span className="trade-item-meta">×{item.quantity}{item.rarity ? ` · ${item.rarity}` : ''}</span>
                      </button>
                      {picked && item.quantity > 1 ? (
                        <input
                          type="number"
                          min={1}
                          max={item.quantity}
                          value={selectedItems[item.id]}
                          onChange={(e) => setQty(item, Number(e.target.value) || 1)}
                          className="trade-qty"
                          aria-label={`Quantity of ${item.name}`}
                        />
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <label className="trade-field">
            <span>Gold you offer (you have {fromCharacter.gold ?? 0} gp)</span>
            <input
              type="number"
              className="trade-gold-input"
              min={0}
              max={fromCharacter.gold ?? 0}
              value={offeredGold}
              onChange={(e) => setOfferedGold(Math.max(0, Math.min(fromCharacter.gold ?? 0, Number(e.target.value) || 0)))}
            />
          </label>

          <label className="trade-field">
            <span>Gold you request</span>
            <input
              type="number"
              className="trade-gold-input"
              min={0}
              value={requestedGold}
              onChange={(e) => setRequestedGold(Math.max(0, Number(e.target.value) || 0))}
            />
          </label>

          <label className="trade-field">
            <span>Message (optional)</span>
            <textarea
              className="trade-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={280}
              rows={2}
              placeholder="e.g. Use this potion if things get hairy."
            />
          </label>
        </div>

        <footer className="trade-modal-footer">
          <button className="trade-btn-secondary" onClick={onClose} disabled={sending}>Cancel</button>
          <button className="trade-btn-primary" onClick={handleSend} disabled={sending || !to || (Object.keys(selectedItems).length === 0 && offeredGold === 0 && requestedGold === 0)}>
            {sending ? 'Sending…' : 'Send offer'}
          </button>
        </footer>
      </div>
    </div>
  );
}

interface IncomingTradeModalProps {
  sessionId: string;
  playerId: string;
  trade: Trade;
  onResolved: (trade: Trade) => void;
  onClose: () => void;
}

export function IncomingTradeModal({ sessionId, playerId, trade, onResolved, onClose }: IncomingTradeModalProps) {
  const { addToast } = useToast();
  const [busy, setBusy] = useState(false);
  const [showCounterPrompt, setShowCounterPrompt] = useState(false);
  const [counterNote, setCounterNote] = useState('');

  const handle = async (action: 'accept' | 'decline') => {
    setBusy(true);
    try {
      const res = await respondTrade(sessionId, trade.id, action, playerId);
      addToast({
        type: action === 'accept' ? 'success' : 'info',
        title: action === 'accept' ? 'Trade accepted' : 'Trade declined',
        message: action === 'accept'
          ? `You received ${trade.offered_items.map((i) => `${i.name ?? i.item_id} ×${i.quantity}`).join(', ')}.`
          : `Declined ${trade.from_player_name}'s offer.`,
      });
      onResolved(res.trade);
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not respond';
      addToast({ type: 'error', title: 'Trade failed', message: msg });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="trade-modal-backdrop" role="dialog" aria-modal="true">
      <div className="trade-modal trade-modal-incoming" onClick={(e) => e.stopPropagation()}>
        <header className="trade-modal-header">
          <h2>🎁 Incoming trade</h2>
          <button className="trade-modal-close" onClick={onClose} aria-label="Close">×</button>
        </header>

        <div className="trade-modal-body">
          <div className="trade-incoming-from">
            <strong>{trade.from_player_name}</strong> offers you:
          </div>
          <ul className="trade-items">
            {trade.offered_items.map((item) => (
              <li key={item.item_id} className="trade-item is-picked">
                <span className="trade-item-row">
                  <span className="trade-item-name">{item.name ?? item.item_id}</span>
                  <span className="trade-item-meta">×{item.quantity}</span>
                </span>
              </li>
            ))}
            {trade.offered_gold > 0 ? (
              <li className="trade-item is-picked trade-item-gold">
                <span className="trade-item-row">
                  <span className="trade-item-name">💰 Gold</span>
                  <span className="trade-item-meta">{trade.offered_gold} gp</span>
                </span>
              </li>
            ) : null}
          </ul>

          {(trade.requested_items.length > 0 || trade.requested_gold > 0) ? (
            <>
              <div className="trade-incoming-from" style={{ marginTop: '0.8rem' }}>In exchange for:</div>
              <ul className="trade-items">
                {trade.requested_items.map((item) => (
                  <li key={item.item_id} className="trade-item">
                    <span className="trade-item-row">
                      <span className="trade-item-name">{item.name ?? item.item_id}</span>
                      <span className="trade-item-meta">×{item.quantity}</span>
                    </span>
                  </li>
                ))}
                {trade.requested_gold > 0 ? (
                  <li className="trade-item trade-item-gold">
                    <span className="trade-item-row">
                      <span className="trade-item-name">💰 Gold</span>
                      <span className="trade-item-meta">{trade.requested_gold} gp</span>
                    </span>
                  </li>
                ) : null}
              </ul>
            </>
          ) : null}

          {trade.note ? (
            <div className="trade-incoming-note">“{trade.note}”</div>
          ) : null}
        </div>

        <footer className="trade-modal-footer">
          <button className="trade-btn-secondary" onClick={() => handle('decline')} disabled={busy}>
            {busy ? '…' : 'Decline'}
          </button>
          <button className="trade-btn-secondary" onClick={() => setShowCounterPrompt(true)} disabled={busy}>
            Counter…
          </button>
          <button className="trade-btn-primary" onClick={() => handle('accept')} disabled={busy}>
            {busy ? '…' : 'Accept'}
          </button>
        </footer>

        {showCounterPrompt ? (
          <div className="trade-counter-prompt">
            <p>
              Send the original offer back to <strong>{trade.from_player_name}</strong> as a counter? They can then accept,
              decline, or counter again. (For complex re-negotiation, decline and create a fresh trade.)
            </p>
            <input
              className="trade-note"
              type="text"
              maxLength={280}
              placeholder="Optional note"
              value={counterNote}
              onChange={(e) => setCounterNote(e.target.value)}
            />
            <div className="trade-counter-actions">
              <button className="trade-btn-secondary" onClick={() => setShowCounterPrompt(false)} disabled={busy}>Back</button>
              <button
                className="trade-btn-primary"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    const res = await counterTrade(sessionId, trade.id, {
                      player_id: playerId,
                      // Offer back what was requested, request back what was offered, swap gold.
                      offered_items: trade.requested_items.map((i) => ({ item_id: i.item_id, quantity: i.quantity })),
                      requested_items: trade.offered_items.map((i) => ({ item_id: i.item_id, quantity: i.quantity })),
                      offered_gold: trade.requested_gold,
                      requested_gold: trade.offered_gold,
                      note: counterNote,
                    });
                    addToast({ type: 'success', title: 'Counter sent', message: `${trade.from_player_name} will see your counter offer.` });
                    onResolved(res.original);
                    onClose();
                  } catch (err) {
                    addToast({ type: 'error', message: err instanceof Error ? err.message : 'Counter failed' });
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Send counter
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

interface OutgoingTradeBadgeProps {
  sessionId: string;
  playerId: string;
  trade: Trade;
  onResolved: (trade: Trade) => void;
}

export function OutgoingTradeBadge({ sessionId, playerId, trade, onResolved }: OutgoingTradeBadgeProps) {
  const { addToast } = useToast();
  const [busy, setBusy] = useState(false);

  const handleCancel = async () => {
    setBusy(true);
    try {
      const res = await cancelTrade(sessionId, trade.id, playerId);
      addToast({ type: 'info', message: 'Trade cancelled.' });
      onResolved(res.trade);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Cancel failed';
      addToast({ type: 'error', message: msg });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="trade-outgoing-badge" role="status">
      <span>Trade with <strong>{trade.to_player_name}</strong> pending…</span>
      <button className="trade-btn-link" onClick={handleCancel} disabled={busy}>Cancel</button>
    </div>
  );
}

// Auto-dismiss helper so a stale modal doesn't get stuck if the offer is
// cancelled/declined by the other side.
export function useAutoCloseOnResolve(trade: Trade | null, onClose: () => void) {
  useEffect(() => {
    if (trade && trade.status !== 'pending') {
      const t = setTimeout(onClose, 2500);
      return () => clearTimeout(t);
    }
  }, [trade, onClose]);
}
