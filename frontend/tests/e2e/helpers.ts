import type { Page } from '@playwright/test';

/** Mock campaign data returned by /api/campaigns */
const MOCK_CAMPAIGNS = [
  {
    id: 'camp-1',
    name: 'Lost Mines',
    description: 'A classic adventure',
    character_ids: ['char-1'],
    world_state: {},
    dm_settings: {},
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

/** Mock game state returned by /api/game/sessions/:id/state */
const MOCK_GAME_STATE = {
  id: 'test-session',
  campaign_id: 'camp-1',
  phase: 'exploration',
  current_scene: 'Welcome to the adventure!',
  players: ['player-1'],
  combat_state: null,
  is_active: true,
};

/** Mock avatar state */
const MOCK_AVATAR = {
  expression: 'neutral',
  is_speaking: false,
  mouth_amplitude: 0,
  gaze: { x: 0, y: 0 },
};

/**
 * Predicate-based route matcher for REST API calls.
 * Uses predicates to avoid matching Vite source files like /src/api/...
 */
function apiPathMatch(pattern: string): (url: URL) => boolean {
  if (pattern === '*') {
    return (url: URL) => url.pathname.startsWith('/api/');
  }
  const regexStr = '^' + pattern.replace(/\*/g, '[^/]+') + '$';
  const regex = new RegExp(regexStr);
  return (url: URL) => regex.test(url.pathname);
}

/**
 * Sets up API route interception for the Home page.
 * Must be called BEFORE page.goto('/').
 */
export async function mockHomePageAPIs(page: Page) {
  // Catch-all first (lowest priority in Playwright's LIFO matching)
  await page.route(apiPathMatch('*'), (route) => {
    route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
  });

  // Specific /api/campaigns route (higher priority)
  await page.route(apiPathMatch('/api/campaigns'), (route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_CAMPAIGNS[0]),
      });
    } else {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_CAMPAIGNS),
      });
    }
  });
}

/**
 * Sets up API route interception for the GameSession page.
 * Must be called BEFORE page.goto('/game/:sessionId').
 */
export async function mockGameSessionAPIs(page: Page) {
  // Mock WebSocket to prevent reconnection loops that block networkidle
  await page.routeWebSocket('**/ws/**', (ws) => {
    ws.onMessage(() => {});
  });

  // Catch-all first (lowest priority in Playwright's LIFO matching)
  await page.route(apiPathMatch('*'), (route) => {
    route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
  });

  await page.route(apiPathMatch('/api/avatar/*'), (route) => {
    if (route.request().method() === 'GET') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_AVATAR),
      });
    } else {
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok": true}' });
    }
  });

  await page.route(apiPathMatch('/api/game/sessions/*/action'), (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ narration: 'The DM responds.', dice_results: [] }),
    });
  });

  await page.route(apiPathMatch('/api/game/sessions/*/state'), (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_GAME_STATE),
    });
  });
}

/**
 * Filters out non-critical console errors that occur because there's no
 * real backend (WebSocket failures, network errors, etc.).
 */
export function filterNonCriticalErrors(errors: string[]): string[] {
  return errors.filter(
    (err) =>
      !err.includes('WebSocket') &&
      !err.includes('ws://') &&
      !err.includes('wss://') &&
      !err.includes('Network request failed') &&
      !err.includes('Failed to fetch') &&
      !err.includes('net::ERR') &&
      !err.includes('404') &&
      !err.includes('502') &&
      !err.includes('ERR_CONNECTION_REFUSED'),
  );
}
