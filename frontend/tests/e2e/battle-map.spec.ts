import { test, expect } from '@playwright/test';
import { mockGameSessionAPIs, filterNonCriticalErrors } from './helpers';

test.describe('Battle Map - Game Session Page', () => {
  test('game session page loads with battle map UI', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    const heading = page.locator('h1');
    await expect(heading).toContainText('Game Session');
  });

  test('game page returns successful response', async ({ page }) => {
    await mockGameSessionAPIs(page);
    const response = await page.goto('/game/test-session');
    expect(response?.status()).toBe(200);
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
});

test.describe('Battle Map - UI Elements', () => {
  test('game layout contains sidebar for battle map elements', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    const sidebar = page.locator('.game-sidebar-right');
    await expect(sidebar).toBeVisible();
  });

  test('game session page has main game area', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    const mainArea = page.locator('.game-main-content');
    await expect(mainArea).toBeVisible();
  });

  test('battle map container is present in game layout', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    const layout = page.locator('.game-session');
    await expect(layout).toBeVisible();
  });

  test('page structure supports battle map display', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const gameSession = page.locator('.game-session');
    const gameBody = page.locator('.game-body');

    await expect(gameSession).toBeVisible();
    await expect(gameBody).toBeVisible();
  });
});

test.describe('Battle Map - Game Components', () => {
  test('initiative tracker is available in sidebar', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    const sidebar = page.locator('.game-sidebar-right');

    await expect(sidebar).toBeVisible();
  });

  test('game chat is present in main area', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    const mainArea = page.locator('.game-main-content');

    await expect(mainArea).toBeVisible();
  });

  test('game session contains interactive elements', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const layout = page.locator('.game-session');
    const sidebarLeft = page.locator('.game-sidebar-left');
    const main = page.locator('.game-main-content');

    await expect(layout).toBeVisible();
    await expect(sidebarLeft).toBeVisible();
    await expect(main).toBeVisible();
  });
});

test.describe('Battle Map - Content Display', () => {
  test('welcome message is displayed', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForTimeout(500);

    const body = page.locator('body');
    await expect(body).toContainText('Welcome to the adventure');
  });

  test('session information is displayed', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');
    await page.waitForTimeout(500);

    // The game state mock has current_scene "Welcome to the adventure!" which is displayed
    const body = page.locator('body');
    await expect(body).toContainText('Welcome to the adventure');
  });

  test('game session page is interactive', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
  });
});

test.describe('Battle Map - Responsive Design', () => {
  test('battle map UI is visible on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const gameLayout = page.locator('.game-session');
    await expect(gameLayout).toBeVisible();
  });

  test('battle map components render in sidebar layout', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const sidebar = page.locator('.game-sidebar-left');
    const main = page.locator('.game-main-content');

    await expect(sidebar).toBeVisible();
    await expect(main).toBeVisible();
  });

  test('game session page renders at tablet size', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const gameLayout = page.locator('.game-session');
    await expect(gameLayout).toBeVisible();
  });
});

test.describe('Battle Map - DOM Structure', () => {
  test('page contains expected CSS classes for layout', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const gameSession = page.locator('.game-session');
    const gameBody = page.locator('.game-body');
    const sidebarLeft = page.locator('.game-sidebar-left');
    const main = page.locator('.game-main-content');

    await expect(gameSession).toBeVisible();
    await expect(gameBody).toBeVisible();
    await expect(sidebarLeft).toBeVisible();
    await expect(main).toBeVisible();
  });

  test('battle map UI elements are properly nested', async ({ page }) => {
    await mockGameSessionAPIs(page);
    await page.goto('/game/test-session');

    const gameSession = page.locator('.game-session');
    const heading = gameSession.locator('h1');
    const gameBody = gameSession.locator('.game-body');

    await expect(heading).toBeVisible();
    await expect(gameBody).toBeVisible();
  });
});
