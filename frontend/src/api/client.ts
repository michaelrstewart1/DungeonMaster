/** Typed API client for the AI Dungeon Master backend. */
import type {
  Campaign,
  CampaignCreate,
  Character,
  CharacterCreate,
  GameSession,
  GameState,
  HealthResponse,
  PlayerAction,
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
    throw new ApiError(response.status, errorText);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
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

export async function importCharacter(format: string, data: Record<string, unknown>): Promise<Character> {
  return request<Character>('/characters/import', {
    method: 'POST',
    body: JSON.stringify({ format, data }),
  });
}

// Game Sessions
export async function createGameSession(campaignId: string): Promise<GameSession> {
  return request<GameSession>('/game/sessions', {
    method: 'POST',
    body: JSON.stringify({ campaign_id: campaignId }),
  });
}

export async function getGameState(sessionId: string): Promise<GameState> {
  return request<GameState>(`/game/sessions/${sessionId}/state`);
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

export { ApiError };
