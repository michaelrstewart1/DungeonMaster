import { useState, useEffect, useCallback } from 'react';
import { getPartyLoot, addPartyLoot, updatePartyGold, distributeLoot } from '../api/client';
import type { LootItemData, PartyLootResponse } from '../api/client';
import type { Character } from '../types';

const RARITY_COLORS: Record<string, string> = {
  common: '#9d9d9d',
  uncommon: '#1eff00',
  rare: '#0070dd',
  'very-rare': '#a335ee',
  legendary: '#ff8000',
};

const TYPE_ICONS: Record<string, string> = {
  weapon: '⚔️',
  armor: '🛡️',
  potion: '🧪',
  scroll: '📜',
  ring: '💍',
  misc: '📦',
};

interface PartyInventoryProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
  /** New items detected from DM narration */
  pendingLoot?: LootItemData[];
  onLootClaimed?: () => void;
  /** Party characters for loot distribution */
  partyCharacters?: Character[];
  /** Callback when loot is distributed (to refresh character state) */
  onLootDistributed?: (characterId: string) => void;
}

export default function PartyInventory({ sessionId, isOpen, onClose, pendingLoot, onLootClaimed, partyCharacters, onLootDistributed }: PartyInventoryProps) {
  const [inventory, setInventory] = useState<PartyLootResponse>({ items: [], gold: 0 });
  const [goldInput, setGoldInput] = useState('');
  const [goldReason, setGoldReason] = useState('');
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [distributing, setDistributing] = useState<Record<number, boolean>>({});
  const [distributeSuccess, setDistributeSuccess] = useState<Record<number, string>>({});

  const fetchLoot = useCallback(async () => {
    try {
      const data = await getPartyLoot(sessionId);
      setInventory(data);
    } catch {
      // silent fail — inventory is optional
    }
  }, [sessionId]);

  useEffect(() => {
    if (isOpen) fetchLoot();
  }, [isOpen, fetchLoot]);

  const handleClaimLoot = async () => {
    if (!pendingLoot?.length) return;
    setLoading(true);
    try {
      const data = await addPartyLoot(sessionId, pendingLoot);
      setInventory(data);
      onLootClaimed?.();
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleGoldChange = async (multiplier: 1 | -1) => {
    const amount = parseInt(goldInput);
    if (isNaN(amount) || amount <= 0) return;
    setLoading(true);
    try {
      const result = await updatePartyGold(sessionId, amount * multiplier, goldReason);
      setInventory(prev => ({ ...prev, gold: result.gold }));
      setGoldInput('');
      setGoldReason('');
    } catch { /* ignore */ }
    setLoading(false);
  };

  const filteredItems = filter === 'all'
    ? inventory.items
    : inventory.items.filter(i => i.item_type === filter);

  // Map filtered items back to their original indices in inventory.items
  const filteredWithIndex = filteredItems.map(item => ({
    item,
    originalIndex: inventory.items.indexOf(item),
  }));

  const typeCount = inventory.items.reduce((acc, item) => {
    acc[item.item_type] = (acc[item.item_type] || 0) + item.quantity;
    return acc;
  }, {} as Record<string, number>);

  const handleDistribute = async (originalIndex: number, characterId: string, quantity: number) => {
    if (!characterId) return;
    setDistributing(prev => ({ ...prev, [originalIndex]: true }));
    try {
      const result = await distributeLoot(sessionId, originalIndex, characterId, quantity);
      setInventory(prev => ({ ...prev, items: result.party_loot as unknown as LootItemData[] }));
      const charName = partyCharacters?.find(c => c.id === characterId)?.name || 'character';
      setDistributeSuccess(prev => ({ ...prev, [originalIndex]: `Given to ${charName}!` }));
      onLootDistributed?.(characterId);
      setTimeout(() => {
        setDistributeSuccess(prev => {
          const next = { ...prev };
          delete next[originalIndex];
          return next;
        });
      }, 2000);
    } catch { /* ignore */ }
    setDistributing(prev => ({ ...prev, [originalIndex]: false }));
  };

  if (!isOpen) return null;

  return (
    <div className="party-inventory-overlay" onClick={onClose}>
      <div className="party-inventory-panel" onClick={e => e.stopPropagation()}>
        <div className="party-inventory-header">
          <h2>🎒 Party Inventory</h2>
          <button className="party-inventory-close" onClick={onClose}>✕</button>
        </div>

        {/* Gold counter */}
        <div className="party-inventory-gold">
          <div className="gold-display">
            <span className="gold-icon">🪙</span>
            <span className="gold-amount">{inventory.gold.toLocaleString()} GP</span>
          </div>
          <div className="gold-controls">
            <input
              type="number"
              value={goldInput}
              onChange={e => setGoldInput(e.target.value)}
              placeholder="Amount"
              className="gold-input"
              min="1"
            />
            <input
              type="text"
              value={goldReason}
              onChange={e => setGoldReason(e.target.value)}
              placeholder="Reason"
              className="gold-reason"
            />
            <button className="gold-btn gold-add" onClick={() => handleGoldChange(1)} disabled={loading}>+</button>
            <button className="gold-btn gold-sub" onClick={() => handleGoldChange(-1)} disabled={loading}>−</button>
          </div>
        </div>

        {/* Pending loot from DM */}
        {pendingLoot && pendingLoot.length > 0 && (
          <div className="pending-loot">
            <h3>✨ New Loot Found!</h3>
            <div className="pending-loot-items">
              {pendingLoot.map((item, i) => (
                <div key={i} className="pending-loot-item" style={{ borderColor: RARITY_COLORS[item.rarity] || RARITY_COLORS.common }}>
                  <span className="item-icon">{TYPE_ICONS[item.item_type] || '📦'}</span>
                  <span className="item-name" style={{ color: RARITY_COLORS[item.rarity] || RARITY_COLORS.common }}>{item.name}</span>
                  {item.quantity > 1 && <span className="item-qty">x{item.quantity}</span>}
                </div>
              ))}
            </div>
            <button className="claim-loot-btn" onClick={handleClaimLoot} disabled={loading}>
              {loading ? 'Adding...' : '🎉 Claim All Loot'}
            </button>
          </div>
        )}

        {/* Filter tabs */}
        <div className="inventory-filters">
          <button className={`inv-filter ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>
            All ({inventory.items.length})
          </button>
          {Object.entries(typeCount).map(([type, count]) => (
            <button key={type} className={`inv-filter ${filter === type ? 'active' : ''}`} onClick={() => setFilter(type)}>
              {TYPE_ICONS[type] || '📦'} {type} ({count})
            </button>
          ))}
        </div>

        {/* Item grid */}
        <div className="inventory-grid">
          {filteredWithIndex.length === 0 ? (
            <div className="inventory-empty">
              <span className="empty-icon">🎒</span>
              <p>No items yet. Adventure awaits!</p>
            </div>
          ) : (
            filteredWithIndex.map(({ item, originalIndex }) => (
              <div
                key={`${originalIndex}-${item.name}`}
                className={`inventory-item rarity-${item.rarity.replace('-', '')}`}
                style={{ borderColor: RARITY_COLORS[item.rarity] || RARITY_COLORS.common }}
              >
                <div className="item-top">
                  <span className="item-icon">{TYPE_ICONS[item.item_type] || '📦'}</span>
                  {item.quantity > 1 && <span className="item-badge">{item.quantity}</span>}
                </div>
                <div className="item-name" style={{ color: RARITY_COLORS[item.rarity] || RARITY_COLORS.common }}>
                  {item.name}
                </div>
                {item.description && <div className="item-desc">{item.description}</div>}
                <div className="item-rarity">{item.rarity}</div>

                {/* Distribution controls */}
                {partyCharacters && partyCharacters.length > 0 && (
                  distributeSuccess[originalIndex] ? (
                    <div className="loot-distribute-success">✓ {distributeSuccess[originalIndex]}</div>
                  ) : (
                    <LootDistributeRow
                      characters={partyCharacters}
                      maxQuantity={item.quantity}
                      distributing={distributing[originalIndex] || false}
                      onDistribute={(charId, qty) => handleDistribute(originalIndex, charId, qty)}
                    />
                  )
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

/** Inline row for distributing one item to a party member */
function LootDistributeRow({
  characters,
  maxQuantity,
  distributing,
  onDistribute,
}: {
  characters: Character[];
  maxQuantity: number;
  distributing: boolean;
  onDistribute: (characterId: string, quantity: number) => void;
}) {
  const [selectedChar, setSelectedChar] = useState('');
  const [qty, setQty] = useState(1);

  return (
    <div className="loot-distribute-row">
      <select
        className="loot-distribute-select"
        value={selectedChar}
        onChange={e => setSelectedChar(e.target.value)}
      >
        <option value="">Give to...</option>
        {characters.map(c => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>
      {maxQuantity > 1 && (
        <input
          className="loot-qty-input"
          type="number"
          min={1}
          max={maxQuantity}
          value={qty}
          onChange={e => setQty(Math.max(1, Math.min(maxQuantity, parseInt(e.target.value) || 1)))}
        />
      )}
      <button
        className="loot-distribute-btn"
        disabled={!selectedChar || distributing}
        onClick={() => onDistribute(selectedChar, qty)}
      >
        {distributing ? '...' : maxQuantity > 1 ? `Give ${qty}` : 'Give'}
      </button>
    </div>
  );
}