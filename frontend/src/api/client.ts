/** Typed API client for the AI Dungeon Master backend. */
import type {
  Campaign,
  CampaignCreate,
  Character,
  CharacterCreate,
  GameState,
  HealthResponse,
  PlayerAction,
  ProgressionData,
  AwardXPResponse,
  TurnResult,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiError extends Error {
  status: number;
  constructor(
    status: number,
    message: string,
  ) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    // Parse FastAPI error responses into human-readable messages
    const friendlyMessage = parseApiError(response.status, errorText);
    throw new ApiError(response.status, friendlyMessage);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

function parseApiError(status: number, raw: string): string {
  try {
    const parsed = JSON.parse(raw);
    // FastAPI validation error: {"detail": [{"msg": "...", "loc": [...]}]}
    if (Array.isArray(parsed.detail)) {
      const fields = parsed.detail.map((e: { loc?: string[]; msg?: string }) => {
        const field = e.loc?.slice(1).join('.') || 'unknown';
        return `${field}: ${e.msg || 'invalid'}`;
      });
      return `Validation error — ${fields.join(', ')}`;
    }
    // FastAPI simple error: {"detail": "Campaign not found"}
    if (typeof parsed.detail === 'string') {
      return parsed.detail;
    }
  } catch { /* not JSON, use raw */ }

  if (status === 404) return 'Not found. The resource may have been deleted.';
  if (status === 422) return 'Invalid request data.';
  if (status >= 500) return 'Server error. Please try again.';
  return raw.length > 200 ? raw.slice(0, 200) + '…' : raw;
}

// Health
export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

// Campaigns
export async function getCampaigns(): Promise<Campaign[]> {
  return request<Campaign[]>('/campaigns');
}

export async function getCampaign(id: string): Promise<Campaign> {
  return request<Campaign>(`/campaigns/${id}`);
}

export async function createCampaign(data: CampaignCreate): Promise<Campaign> {
  return request<Campaign>('/campaigns', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateCampaign(id: string, data: Partial<CampaignCreate>): Promise<Campaign> {
  return request<Campaign>(`/campaigns/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteCampaign(id: string): Promise<void> {
  return request<void>(`/campaigns/${id}`, { method: 'DELETE' });
}

export async function randomizeCampaign(): Promise<Campaign> {
  return request<Campaign>('/campaigns/randomize', { method: 'POST' });
}

// Characters
export async function getCharacters(campaignId?: string): Promise<Character[]> {
  const query = campaignId ? `?campaign_id=${campaignId}` : '';
  return request<Character[]>(`/characters${query}`);
}

export async function getCharacter(id: string): Promise<Character> {
  return request<Character>(`/characters/${id}`);
}

export async function createCharacter(data: CharacterCreate): Promise<Character> {
  return request<Character>('/characters', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateCharacter(id: string, data: Partial<CharacterCreate>): Promise<Character> {
  return request<Character>(`/characters/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteCharacter(id: string): Promise<void> {
  return request<void>(`/characters/${id}`, { method: 'DELETE' });
}

export async function generatePortrait(characterId: string): Promise<Character> {
  return request<Character>(`/characters/${characterId}/generate-portrait`, {
    method: 'POST',
  });
}

export async function importCharacter(format: string, data: Record<string, unknown>): Promise<Character> {
  return request<Character>('/characters/import', {
    method: 'POST',
    body: JSON.stringify({ format, data }),
  });
}

export async function getCharacterProgression(characterId: string): Promise<ProgressionData> {
  return request<ProgressionData>(`/characters/${characterId}/progression`);
}

export async function awardXP(characterId: string, xp: number, reason: string): Promise<AwardXPResponse> {
  return request<AwardXPResponse>(`/characters/${characterId}/award-xp`, {
    method: 'POST',
    body: JSON.stringify({ xp, reason }),
  });
}

// Game Sessions
export async function createGameSession(campaignId: string): Promise<{ id: string }> {
  return request<{ id: string }>('/game/sessions', {
    method: 'POST',
    body: JSON.stringify({
      campaign_id: campaignId,
      current_scene: 'Your adventure begins...',
    }),
  });
}

export async function getGameState(sessionId: string): Promise<GameState> {
  const raw = await request<GameState & { current_phase?: string }>(`/game/sessions/${sessionId}/state`);
  // Backend returns current_phase, frontend expects phase
  if (raw.current_phase && !raw.phase) {
    (raw as unknown as Record<string, unknown>).phase = raw.current_phase;
  }
  return raw;
}

export async function submitAction(sessionId: string, action: PlayerAction): Promise<TurnResult> {
  return request<TurnResult>(`/game/sessions/${sessionId}/action`, {
    method: 'POST',
    body: JSON.stringify(action),
  });
}

export async function startCombat(sessionId: string, enemies: Record<string, unknown>[] = []): Promise<GameState> {
  return request<GameState>(`/game/sessions/${sessionId}/start-combat`, {
    method: 'POST',
    body: JSON.stringify({ enemies }),
  });
}

export async function endCombat(sessionId: string): Promise<GameState> {
  return request<GameState>(`/game/sessions/${sessionId}/end-combat`, {
    method: 'POST',
  });
}

export async function getSessionGreeting(sessionId: string): Promise<string> {
  const result = await request<{ greeting: string }>(`/game/sessions/${sessionId}/greeting`);
  return result.greeting;
}

export interface SessionRecapData {
  has_recap: boolean;
  campaign_name: string;
  recap_text: string;
}

export async function getSessionRecap(sessionId: string): Promise<SessionRecapData> {
  return request<SessionRecapData>(`/game/sessions/${sessionId}/recap`);
}

// Party Inventory / Loot
export interface LootItemData {
  name: string;
  description: string;
  rarity: string;
  quantity: number;
  item_type: string;
}

export interface PartyLootResponse {
  items: LootItemData[];
  gold: number;
}

export async function getPartyLoot(sessionId: string): Promise<PartyLootResponse> {
  return request<PartyLootResponse>(`/game/sessions/${sessionId}/loot`);
}

export async function addPartyLoot(sessionId: string, items: LootItemData[]): Promise<PartyLootResponse> {
  return request<PartyLootResponse>(`/game/sessions/${sessionId}/loot`, {
    method: 'POST',
    body: JSON.stringify({ items }),
  });
}

export async function updatePartyGold(sessionId: string, amount: number, reason: string): Promise<{ gold: number; transaction: string }> {
  return request<{ gold: number; transaction: string }>(`/game/sessions/${sessionId}/gold`, {
    method: 'POST',
    body: JSON.stringify({ amount, reason }),
  });
}

export { ApiError };
