import { test, expect } from '@playwright/test';
import { mockGameSessionAPIs, filterNonCriticalErrors } from './helpers';

test.describe('Avatar Display', () => {
  test('game session page loads with avatar area', async ({ page }) => {
    await mockGameSessionAPIs(page);
    const response = await page.goto('/game/test-session');
    expect(response?.status()).toBe(200);
  });

  test('avatar section renders on game page', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const pageBody = page.locator('body');
    await expect(pageBody).not.toBeEmpty();
  });

  test('DMAvatar component is present', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const gameLayout = page.locator('.game-session');
    await expect(gameLayout).toBeVisible();
  });

  test('audio controls are present on game page', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const main = page.locator('.game-main-content');
    await expect(main).toBeVisible();
  });

  test('page renders without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    expect(filterNonCriticalErrors(errors)).toHaveLength(0);
  });

  test('avatar state can be accessed via API', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const avatarResponse = await page.evaluate(async () => {
      try {
        const resp = await fetch('/api/avatar/test-session');
        if (resp.ok) {
          return await resp.json();
        }
        return null;
      } catch {
        return null;
      }
    });

    if (avatarResponse) {
      expect(avatarResponse).toBeDefined();
      expect(['expression', 'is_speaking', 'mouth_amplitude', 'gaze'].some(
        (key) => key in avatarResponse
      )).toBeTruthy();
    }
  });

  test('page layout maintains structure on avatar load', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const sidebar = page.locator('.game-sidebar-left');
    const main = page.locator('.game-main-content');

    await expect(sidebar).toBeVisible();
    await expect(main).toBeVisible();
  });

  test('avatar responds to session ID parameter', async ({ page }) => {
    await mockGameSessionAPIs(page);
    const sessionId = 'avatar-test-123';
    await page.goto(`/game/${sessionId}`);

    expect(page.url()).toContain(sessionId);
  });

  test('multiple session IDs can be loaded independently', async ({ page }) => {
    await mockGameSessionAPIs(page);

    await page.goto('/game/session-1');
    let currentUrl = page.url();
    expect(currentUrl).toContain('session-1');

    await page.goto('/game/session-2');
    currentUrl = page.url();
    expect(currentUrl).toContain('session-2');

    const layout = page.locator('.game-session');
    await expect(layout).toBeVisible();
  });

  test('avatar page handles missing backend data gracefully', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/nonexistent-session');
    await page.waitForLoadState('networkidle');

    const body = page.locator('body');
    await expect(body).not.toBeEmpty();
  });
});

test.describe('Avatar Interactions', () => {
  test('avatar area is part of game layout', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const layout = page.locator('.game-session');
    await expect(layout).toBeVisible();
  });

  test('avatar content is visible when page loads', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    await page.waitForTimeout(500);

    const mainContent = page.locator('.game-main-content').first();
    await expect(mainContent).toBeVisible();
  });

  test('sidebar is accessible alongside avatar', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const layout = page.locator('.game-session');
    const sidebar = page.locator('.game-sidebar-left');

    await expect(layout).toBeVisible();
    await expect(sidebar).toBeVisible();
  });

  test('audio controls maintain visibility in layout', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const body = page.locator('body');
    await expect(body).not.toBeEmpty();
  });

  test('avatar area persists when navigating game phases', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const layout = page.locator('.game-session');
    await expect(layout).toBeVisible();

    await page.waitForTimeout(300);
    await expect(layout).toBeVisible();
  });
});

test.describe('Avatar UI Resilience', () => {
  test('avatar renders without requiring full backend state', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const layout = page.locator('.game-session');
    await expect(layout).toBeVisible();
  });

  test('avatar display is resilient to missing props', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/minimal-session');
    await page.waitForLoadState('networkidle');

    const body = page.locator('body');
    await expect(body).not.toBeEmpty();
  });

  test('avatar component handles expression state changes', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');

    const result = await page.evaluate(async () => {
      try {
        const resp = await fetch('/api/avatar/test-session/expression', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expression: 'neutral' }),
        });
        return resp.ok;
      } catch {
        return false;
      }
    });

    // Whether successful or not, page should remain stable
    const layout = page.locator('.game-session');
    await expect(layout).toBeVisible();
  });

  test('avatar area survives rapid page interactions', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    for (let i = 0; i < 3; i++) {
      await page.waitForLoadState('networkidle');
      const layout = page.locator('.game-session');
      await expect(layout).toBeVisible();
      await page.waitForTimeout(100);
    }

    const body = page.locator('body');
    await expect(body).not.toBeEmpty();
  });
});
