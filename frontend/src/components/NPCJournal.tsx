import { useEffect, useRef, useState } from 'react';
import '../pages/GameSession.css';

export interface NPCData {
  name: string;
  npc_type: string;
  disposition: 'friendly' | 'neutral' | 'hostile' | 'unknown';
  location: string;
  notes: string;
}

interface NPCJournalProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
  onNPCDetected?: (npc: NPCData) => void;
}

const NPC_EMOJIS: Record<string, string> = {
  merchant: '🏪',
  guard: '⚔️',
  wizard: '🧙',
  noble: '👑',
  monster: '👹',
  cleric: '⛪',
  rogue: '🗡️',
  bard: '🎵',
  scholar: '📖',
  bartender: '🍺',
  innkeeper: '🏨',
  blacksmith: '🔨',
  default: '👤',
};

const DISPOSITION_COLORS: Record<string, string> = {
  friendly: '#4CAF50',
  neutral: '#D4A846',
  hostile: '#C94444',
  unknown: '#999999',
};

/**
 * Detect NPC mentions in DM narration.
 * Looks for quoted speech with attribution like:
 * - "Hello," said the barkeep
 * - The wizard Gandalf speaks
 * - "Welcome," says the innkeeper
 * - The merchant speaks
 */
export function detectNPCMention(text: string): { name: string; type: string } | null {
  // Pattern: "quote" verb (said|says|speaks) [the] (type) (name)?
  const patterns = [
    // "Hello," said the barkeep
    /"[^"]*"\s+(said|says|spoke)\s+the\s+(\w+)(?:\s+(\w+))?/i,
    // The wizard Gandalf speaks
    /the\s+(\w+)\s+(\w+)\s+(speaks|said|says)/i,
    // the barkeep says "..."
    /the\s+(\w+)\s+(?:\w+\s)*(?:says|said|speaks)\s+"[^"]*"/i,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      // Try to extract type and name
      let type = '';
      let name = '';

      if (match[2] && match[3]) {
        // "quote" said the type name
        type = match[2].toLowerCase();
        name = match[3].charAt(0).toUpperCase() + match[3].slice(1);
      } else if (match[1]) {
        // the type name speaks OR the type says
        type = match[1].toLowerCase();
        if (match[2] && match[2] !== 'speaks' && match[2] !== 'says') {
          name = match[2].charAt(0).toUpperCase() + match[2].slice(1);
        }
      }

      if (type) {
        return {
          name: name || `${type.charAt(0).toUpperCase()}${type.slice(1)}`,
          type,
        };
      }
    }
  }

  return null;
}

export function NPCJournal({ sessionId, isOpen, onClose, onNPCDetected }: NPCJournalProps) {
  const [npcs, setNpcs] = useState<NPCData[]>([]);
  const [filterDisposition, setFilterDisposition] = useState<string>('all');
  const [searchText, setSearchText] = useState('');
  const [editingNpc, setEditingNpc] = useState<NPCData | null>(null);
  const [editNotes, setEditNotes] = useState('');
  const [newNpcName, setNewNpcName] = useState('');
  const [newNpcType, setNewNpcType] = useState('');
  const [newNpcDisposition, setNewNpcDisposition] = useState<'friendly' | 'neutral' | 'hostile' | 'unknown'>('unknown');
  const [newNpcLocation, setNewNpcLocation] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  // Load NPCs on mount
  useEffect(() => {
    loadNpcs();
  }, [sessionId]);

  // Handle N key to toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'n' && !isOpen) {
        // Don't open if typing in an input
        if (
          e.target instanceof HTMLInputElement ||
          e.target instanceof HTMLTextAreaElement
        ) {
          return;
        }
        // Open journal
        // This would be handled by the parent component
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Close on escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Close when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  async function loadNpcs() {
    try {
      const response = await fetch(`/api/game/sessions/${sessionId}/npcs`);
      if (response.ok) {
        const data = await response.json();
        setNpcs(data.npcs || []);
      }
    } catch (err) {
      console.error('Failed to load NPCs:', err);
    }
  }

  async function saveNpc(npc: NPCData) {
    try {
      const response = await fetch(`/api/game/sessions/${sessionId}/npcs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(npc),
      });

      if (response.ok) {
        const data = await response.json();
        setNpcs(data.npcs || []);
        setEditingNpc(null);
        setEditNotes('');
        if (onNPCDetected) {
          onNPCDetected(npc);
        }
      }
    } catch (err) {
      console.error('Failed to save NPC:', err);
    }
  }

  function handleAddNpc() {
    if (!newNpcName.trim() || !newNpcType.trim()) return;

    const npc: NPCData = {
      name: newNpcName,
      npc_type: newNpcType,
      disposition: newNpcDisposition,
      location: newNpcLocation,
      notes: '',
    };

    saveNpc(npc);
    setNewNpcName('');
    setNewNpcType('');
    setNewNpcLocation('');
    setNewNpcDisposition('unknown');
  }

  function handleUpdateNotes() {
    if (!editingNpc) return;

    const updated: NPCData = {
      ...editingNpc,
      notes: editNotes,
    };

    saveNpc(updated);
  }

  function getFilteredNpcs() {
    return npcs.filter((npc) => {
      const matchesDisposition =
        filterDisposition === 'all' || npc.disposition === filterDisposition;
      const matchesSearch =
        searchText === '' ||
        npc.name.toLowerCase().includes(searchText.toLowerCase()) ||
        npc.npc_type.toLowerCase().includes(searchText.toLowerCase());
      return matchesDisposition && matchesSearch;
    });
  }

  const getEmoji = (type: string) => NPC_EMOJIS[type.toLowerCase()] || NPC_EMOJIS.default;
  const getColor = (disposition: string) => DISPOSITION_COLORS[disposition] || DISPOSITION_COLORS.unknown;

  const filteredNpcs = getFilteredNpcs();

  if (!isOpen) return null;

  return (
    <div className="npc-journal-overlay">
      <div className="npc-journal-modal" ref={containerRef}>
        <div className="npc-journal-header">
          <h2 className="npc-journal-title">Character Relations & NPC Journal</h2>
          <button className="npc-journal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="npc-journal-toolbar">
          <input
            type="text"
            placeholder="Search NPCs by name or type..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="npc-search-input"
          />

          <select
            value={filterDisposition}
            onChange={(e) => setFilterDisposition(e.target.value)}
            className="npc-filter-select"
          >
            <option value="all">All Dispositions</option>
            <option value="friendly">Friendly</option>
            <option value="neutral">Neutral</option>
            <option value="hostile">Hostile</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>

        <div className="npc-journal-body">
          {/* Existing NPCs list */}
          {filteredNpcs.length > 0 && (
            <div className="npc-list">
              {filteredNpcs.map((npc, idx) => (
                <div key={idx} className="npc-card">
                  <div className="npc-card-header">
                    <span className="npc-emoji">{getEmoji(npc.npc_type)}</span>
                    <div className="npc-card-title-area">
                      <h3 className="npc-card-name">{npc.name}</h3>
                      <p className="npc-card-type">{npc.npc_type}</p>
                    </div>
                    <div
                      className="npc-disposition-badge"
                      style={{ backgroundColor: getColor(npc.disposition) }}
                      title={npc.disposition}
                    >
                      {npc.disposition}
                    </div>
                  </div>

                  {npc.location && (
                    <p className="npc-location">
                      <strong>Last Seen:</strong> {npc.location}
                    </p>
                  )}

                  <div className="npc-notes-area">
                    {editingNpc === npc ? (
                      <>
                        <textarea
                          value={editNotes}
                          onChange={(e) => setEditNotes(e.target.value)}
                          placeholder="Add notes about this NPC..."
                          className="npc-notes-edit"
                          rows={3}
                        />
                        <div className="npc-notes-controls">
                          <button
                            onClick={handleUpdateNotes}
                            className="npc-btn npc-btn-save"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingNpc(null)}
                            className="npc-btn npc-btn-cancel"
                          >
                            Cancel
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <p className="npc-notes-display">{npc.notes || '(no notes)'}</p>
                        <button
                          onClick={() => {
                            setEditingNpc(npc);
                            setEditNotes(npc.notes);
                          }}
                          className="npc-btn npc-btn-edit"
                        >
                          Edit Notes
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {filteredNpcs.length === 0 && npcs.length > 0 && (
            <p className="npc-empty-filtered">No NPCs match your filters.</p>
          )}

          {npcs.length === 0 && (
            <p className="npc-empty">No NPCs encountered yet. Add one below or they'll appear automatically when mentioned in narration.</p>
          )}
        </div>

        {/* Add new NPC form */}
        <div className="npc-journal-footer">
          <div className="npc-add-form">
            <h3 className="npc-add-title">Add New NPC</h3>
            <div className="npc-add-inputs">
              <input
                type="text"
                placeholder="Name"
                value={newNpcName}
                onChange={(e) => setNewNpcName(e.target.value)}
                className="npc-input npc-input-name"
              />
              <input
                type="text"
                placeholder="Type (wizard, merchant, guard, etc.)"
                value={newNpcType}
                onChange={(e) => setNewNpcType(e.target.value)}
                className="npc-input npc-input-type"
              />
              <input
                type="text"
                placeholder="Last Location"
                value={newNpcLocation}
                onChange={(e) => setNewNpcLocation(e.target.value)}
                className="npc-input npc-input-location"
              />
              <select
                value={newNpcDisposition}
                onChange={(e) =>
                  setNewNpcDisposition(
                    e.target.value as 'friendly' | 'neutral' | 'hostile' | 'unknown'
                  )
                }
                className="npc-input npc-input-disposition"
              >
                <option value="unknown">Unknown</option>
                <option value="friendly">Friendly</option>
                <option value="neutral">Neutral</option>
                <option value="hostile">Hostile</option>
              </select>
              <button onClick={handleAddNpc} className="npc-btn npc-btn-add">
                Add NPC
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NPCJournal;
