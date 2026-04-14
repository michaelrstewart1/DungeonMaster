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

export type Alignment =
  | 'lawful-good' | 'neutral-good' | 'chaotic-good'
  | 'lawful-neutral' | 'true-neutral' | 'chaotic-neutral'
  | 'lawful-evil' | 'neutral-evil' | 'chaotic-evil';

// Character
export interface CharacterCreate {
  name: string;
  race: Race;
  class_name: CharacterClass;
  level: number;
  hp: number;
  max_hp?: number;
  ac: number;
  experience_points?: number;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  campaign_id?: string;
  portrait_url?: string;
  // New 5e fields
  subrace?: string;
  subclass?: string;
  background?: string;
  alignment?: string;
  speed?: number;
  hit_dice?: string;
  skills?: string[];
  saving_throws?: string[];
  languages?: string[];
  tool_proficiencies?: string[];
  armor_proficiencies?: string[];
  weapon_proficiencies?: string[];
  features?: string[];
  spells_known?: string[];
  cantrips_known?: string[];
  equipment?: string[];
  personality_traits?: string;
  ideals?: string;
  bonds?: string;
  flaws?: string;
  backstory?: string;
}

export interface Character extends CharacterCreate {
  id: string;
  conditions: string[];
  inventory: string[];
  proficiency_bonus: number;
  portrait_url?: string;
  experience_points: number;
}

// Campaign
export interface CampaignCreate {
  name: string;
  description: string;
  world_state?: Record<string, unknown>;
  dm_settings?: Record<string, unknown>;
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
  campaign_id?: string;
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
  mood?: 'dark' | 'warm' | 'peaceful' | 'combat' | 'mystical' | 'neutral';
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

// XP / Progression
export interface Milestone {
  level: number;
  label: string;
  reached: boolean;
}

export interface ProgressionData {
  level: number;
  xp: number;
  xp_to_next: number;
  xp_progress_pct: number;
  milestones: Milestone[];
}

export interface AwardXPResponse {
  character: Character;
  leveled_up: boolean;
  new_level: number | null;
}

export interface EnvironmentData {
  time_of_day: 'dawn' | 'morning' | 'noon' | 'afternoon' | 'dusk' | 'evening' | 'night' | 'midnight';
  weather: 'clear' | 'cloudy' | 'rain' | 'storm' | 'snow' | 'fog' | 'wind';
  temperature: 'freezing' | 'cold' | 'cool' | 'mild' | 'warm' | 'hot';
  season: 'spring' | 'summer' | 'autumn' | 'winter';
}
