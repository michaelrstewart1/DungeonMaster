import { useState, useEffect, useCallback } from 'react';
import { getPendingLevelUps, applyLevelUp } from '../api/client';
import type { Character, PendingLevelUp, LevelUpChoices } from '../types';

const HIT_DICE: Record<string, number> = {
  barbarian: 12, fighter: 10, paladin: 10, ranger: 10,
  bard: 8, cleric: 8, druid: 8, monk: 8, rogue: 8, warlock: 8,
  sorcerer: 6, wizard: 6,
};

const ABILITY_NAMES = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'] as const;
const ABILITY_SHORT: Record<string, string> = {
  strength: 'STR', dexterity: 'DEX', constitution: 'CON',
  intelligence: 'INT', wisdom: 'WIS', charisma: 'CHA',
};

const ASI_LEVELS = new Set([4, 8, 12, 16, 19]);

interface LevelUpModalProps {
  character: Character;
  isOpen: boolean;
  onClose: () => void;
  onLevelUpComplete: (updated: Character) => void;
}

export default function LevelUpModal({ character, isOpen, onClose, onLevelUpComplete }: LevelUpModalProps) {
  const [pending, setPending] = useState<PendingLevelUp[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // HP choice
  const [hpMethod, setHpMethod] = useState<'average' | 'roll'>('average');
  const [hpRoll, setHpRoll] = useState<number | null>(null);

  // ASI choice
  const [asiMode, setAsiMode] = useState<'asi' | 'feat'>('asi');
  const [asiChoices, setAsiChoices] = useState<Record<string, number>>({});
  const [featName, setFeatName] = useState('');

  const hitDie = HIT_DICE[character.class_name?.toLowerCase()] || 8;
  const conMod = Math.floor((character.constitution - 10) / 2);
  const averageHP = Math.max(1, Math.floor(hitDie / 2 + 1) + conMod);

  const currentLevelUp = pending[0] ?? null;
  const isASILevel = currentLevelUp ? ASI_LEVELS.has(currentLevelUp.to_level) : false;

  const fetchPending = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getPendingLevelUps(character.id);
      setPending(data.pending.filter(p => !p.choices_made));
    } catch {
      setPending([]);
    }
    setLoading(false);
  }, [character.id]);

  useEffect(() => {
    if (isOpen) {
      fetchPending();
      setError(null);
      setSuccess(null);
      resetChoices();
    }
  }, [isOpen, fetchPending]);

  const resetChoices = () => {
    setHpMethod('average');
    setHpRoll(null);
    setAsiMode('asi');
    setAsiChoices({});
    setFeatName('');
  };

  const rollHP = () => {
    const roll = Math.floor(Math.random() * hitDie) + 1;
    setHpRoll(roll);
  };

  const totalASI = Object.values(asiChoices).reduce((a, b) => a + b, 0);

  const handleASIChange = (ability: string, delta: number) => {
    const currentVal = asiChoices[ability] || 0;
    const newVal = currentVal + delta;
    if (newVal < 0 || newVal > 2) return;
    if (totalASI + delta > 2) return;
    // Don't exceed ability score cap of 20
    const currentAbilityScore = (character as unknown as Record<string, number>)[ability] || 10;
    if (currentAbilityScore + newVal > 20) return;

    setAsiChoices(prev => {
      const next = { ...prev, [ability]: newVal };
      if (next[ability] === 0) delete next[ability];
      return next;
    });
  };

  const canSubmit = () => {
    if (!currentLevelUp) return false;
    // HP: always valid (average or rolled)
    if (hpMethod === 'roll' && hpRoll === null) return false;
    // ASI: must allocate exactly 2 points or choose a feat
    if (isASILevel) {
      if (asiMode === 'asi' && totalASI !== 2) return false;
      if (asiMode === 'feat' && !featName.trim()) return false;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!canSubmit()) return;
    setSubmitting(true);
    setError(null);

    const choices: LevelUpChoices = {
      hp_roll: hpMethod === 'roll' ? hpRoll : null,
    };
    if (isASILevel) {
      if (asiMode === 'feat') {
        choices.feat = featName.trim();
      } else {
        choices.ability_score_increase = asiChoices;
      }
    }

    try {
      const result = await applyLevelUp(character.id, choices);
      const hpGained = result.hp_gained;
      setSuccess(`Level ${currentLevelUp!.to_level} achieved! +${hpGained} HP`);

      if (result.remaining_level_ups > 0) {
        // More level-ups queued — refresh and reset for next one
        setTimeout(() => {
          setSuccess(null);
          resetChoices();
          fetchPending();
        }, 1500);
      } else {
        // All done — close after brief celebration
        setTimeout(() => {
          onLevelUpComplete(result.character as Character);
          onClose();
        }, 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply level-up');
    }
    setSubmitting(false);
  };

  if (!isOpen) return null;

  return (
    <div className="levelup-overlay" onClick={onClose}>
      <div className="levelup-modal" onClick={e => e.stopPropagation()}>
        {/* Header with glow effect */}
        <div className="levelup-header">
          <div className="levelup-stars">✦ ✦ ✦</div>
          <h2>⬆ Level Up!</h2>
          <p className="levelup-subtitle">
            {character.name} — Level {currentLevelUp?.from_level ?? '?'} → {currentLevelUp?.to_level ?? '?'}
          </p>
          {pending.length > 1 && (
            <div className="levelup-queue-badge">{pending.length} level-ups pending</div>
          )}
          <button className="levelup-close" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="levelup-loading">
            <div className="levelup-spinner" />
            <p>Loading level-up data...</p>
          </div>
        ) : !currentLevelUp ? (
          <div className="levelup-empty">
            <p>No pending level-ups for {character.name}.</p>
            <button className="levelup-btn" onClick={onClose}>Close</button>
          </div>
        ) : (
          <div className="levelup-body">
            {/* HP Section */}
            <div className="levelup-section">
              <h3>❤️ Hit Points</h3>
              <p className="levelup-hint">
                Hit Die: d{hitDie} | CON modifier: {conMod >= 0 ? '+' : ''}{conMod}
              </p>
              <div className="hp-choice-group">
                <label className={`hp-choice ${hpMethod === 'average' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="hp-method"
                    checked={hpMethod === 'average'}
                    onChange={() => setHpMethod('average')}
                  />
                  <span className="hp-choice-label">Take Average</span>
                  <span className="hp-choice-value">+{averageHP} HP</span>
                </label>
                <label className={`hp-choice ${hpMethod === 'roll' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="hp-method"
                    checked={hpMethod === 'roll'}
                    onChange={() => setHpMethod('roll')}
                  />
                  <span className="hp-choice-label">Roll</span>
                  {hpMethod === 'roll' && (
                    <div className="hp-roll-area">
                      <button className="roll-btn" onClick={rollHP} type="button">
                        🎲 Roll d{hitDie}
                      </button>
                      {hpRoll !== null && (
                        <span className="hp-roll-result">
                          Rolled {hpRoll} → +{Math.max(1, hpRoll + conMod)} HP
                        </span>
                      )}
                    </div>
                  )}
                </label>
              </div>
            </div>

            {/* ASI Section (only at ASI levels) */}
            {isASILevel && (
              <div className="levelup-section">
                <h3>📊 Ability Score Improvement</h3>
                <div className="asi-mode-toggle">
                  <button
                    className={`asi-tab ${asiMode === 'asi' ? 'active' : ''}`}
                    onClick={() => setAsiMode('asi')}
                  >
                    Ability Scores (+2)
                  </button>
                  <button
                    className={`asi-tab ${asiMode === 'feat' ? 'active' : ''}`}
                    onClick={() => setAsiMode('feat')}
                  >
                    Choose a Feat
                  </button>
                </div>

                {asiMode === 'asi' ? (
                  <div className="asi-grid">
                    <div className="asi-budget">Points remaining: {2 - totalASI}</div>
                    {ABILITY_NAMES.map(ability => {
                      const currentScore = (character as unknown as Record<string, number>)[ability] || 10;
                      const increase = asiChoices[ability] || 0;
                      const atCap = currentScore + increase >= 20;
                      return (
                        <div key={ability} className="asi-row">
                          <span className="asi-label">{ABILITY_SHORT[ability]}</span>
                          <span className="asi-current">{currentScore}</span>
                          <button
                            className="asi-btn"
                            onClick={() => handleASIChange(ability, -1)}
                            disabled={increase <= 0}
                          >−</button>
                          <span className={`asi-increase ${increase > 0 ? 'active' : ''}`}>
                            {increase > 0 ? `+${increase}` : '—'}
                          </span>
                          <button
                            className="asi-btn"
                            onClick={() => handleASIChange(ability, 1)}
                            disabled={totalASI >= 2 || atCap}
                          >+</button>
                          {increase > 0 && (
                            <span className="asi-new">→ {currentScore + increase}</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="feat-choice">
                    <input
                      type="text"
                      className="feat-input"
                      value={featName}
                      onChange={e => setFeatName(e.target.value)}
                      placeholder="Enter feat name (e.g., Alert, Lucky, Sharpshooter)"
                    />
                    <p className="levelup-hint">
                      Choose any feat from the Player's Handbook or SRD.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Error / Success */}
            {error && <div className="levelup-error">⚠️ {error}</div>}
            {success && <div className="levelup-success">🎉 {success}</div>}

            {/* Submit */}
            <div className="levelup-actions">
              <button className="levelup-btn secondary" onClick={onClose}>
                Decide Later
              </button>
              <button
                className="levelup-btn primary"
                onClick={handleSubmit}
                disabled={!canSubmit() || submitting}
              >
                {submitting ? 'Applying...' : `Confirm Level ${currentLevelUp.to_level}`}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
