/** Shared TypeScript types matching backend Pydantic schemas. */

// Enums
export type Race =
  | 'human' | 'elf' | 'dwarf' | 'halfling' | 'gnome'
  | 'half-elf' | 'half-orc' | 'tiefling' | 'dragonborn';

export type CharacterClass =
  | 'barbarian' | 'bard' | 'cleric' | 'druid' | 'fighter'
  | 'monk' | 'paladin' | 'ranger' | 'rogue' | 'sorcerer'
  | 'warlock' | 'wizard';

export type GamePhase = 'lobby' | 'exploration' | 'combat' | 'rest' | 'shopping' | 'dialogue';
export type TerrainType = 'empty' | 'wall' | 'water' | 'difficult' | 'pit';

// Character
export interface CharacterCreate {
  name: string;
  race: Race;
  class_name: CharacterClass;
  level: number;
  hp: number;
  max_hp: number;
  ac: number;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface Character extends CharacterCreate {
  id: string;
  conditions: string[];
  inventory: string[];
  proficiency_bonus: number;
}

// Campaign
export interface CampaignCreate {
  name: string;
  description: string;
}

export interface Campaign extends CampaignCreate {
  id: string;
  character_ids: string[];
  world_state: Record<string, unknown>;
  dm_settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Game State
export interface CombatState {
  initiative_order: string[];
  current_turn_index: number;
  round_number: number;
}

export interface GameState {
  phase: GamePhase;
  current_scene: string;
  narrative_history: string[];
  combat_state: CombatState | null;
  active_effects: Record<string, unknown>[];
}

// Game Session
export interface GameSession {
  id: string;
  campaign_id: string;
  phase: GamePhase;
  turn_count: number;
  players: string[];
}

// Actions & Results
export interface PlayerAction {
  type: 'attack' | 'cast_spell' | 'ability_check' | 'move' | 'interact' | 'speak';
  target?: string;
  details?: Record<string, unknown>;
  message?: string;
}

export interface TurnResult {
  turn_number: number;
  narration: string;
  phase: string;
  action_result?: {
    action_type: string;
    success: boolean;
    description: string;
    damage_dealt: number;
    healing_done: number;
  };
}

// Dice
export interface DiceResult {
  notation: string;
  rolls: number[];
  modifier: number;
  total: number;
  is_critical: boolean;
  is_fumble: boolean;
}

// Map
export interface TokenPosition {
  entity_id: string;
  x: number;
  y: number;
}

export interface GameMap {
  id: string;
  width: number;
  height: number;
  terrain: TerrainType[][];
  tokens: TokenPosition[];
  fog_of_war: boolean[][];
}

// Health
export interface HealthResponse {
  status: string;
  version: string;
}
