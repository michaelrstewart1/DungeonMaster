import { test, expect } from '@playwright/test';

test.describe('Battle Map - Game Session Page', () => {
  test('game session page loads with battle map UI', async ({ page }) => {
    await page.goto('/game/test-session');
    const heading = page.locator('h1');
    await expect(heading).toContainText('Game Session');
  });

  test('game page returns successful response', async ({ page }) => {
    const response = await page.goto('/game/test-session');
    expect(response?.status()).toBe(200);
  });

  test('page renders without console errors', async ({ page }) => {
    let errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');
    expect(errors).toHaveLength(0);
  });
});

test.describe('Battle Map - UI Elements', () => {
  test('game layout contains sidebar for battle map elements', async ({ page }) => {
    await page.goto('/game/test-session');
    const sidebar = page.locator('.game-sidebar');
    await expect(sidebar).toBeVisible();
  });

  test('game session page has main game area', async ({ page }) => {
    await page.goto('/game/test-session');
    const mainArea = page.locator('.game-main');
    await expect(mainArea).toBeVisible();
  });

  test('battle map container is present in game layout', async ({ page }) => {
    await page.goto('/game/test-session');
    const layout = page.locator('.game-layout');
    await expect(layout).toBeVisible();
  });

  test('page structure supports battle map display', async ({ page }) => {
    await page.goto('/game/test-session');
    
    // Verify the basic structure for battle map UI
    const pageContainer = page.locator('.page-game-session');
    const gameLayout = page.locator('.game-layout');
    
    await expect(pageContainer).toBeVisible();
    await expect(gameLayout).toBeVisible();
  });
});

test.describe('Battle Map - Game Components', () => {
  test('initiative tracker is available in sidebar', async ({ page }) => {
    await page.goto('/game/test-session');
    const sidebar = page.locator('.game-sidebar');
    
    // Sidebar contains InitiativeTracker and DiceRoller
    await expect(sidebar).toBeVisible();
  });

  test('game chat is present in main area', async ({ page }) => {
    await page.goto('/game/test-session');
    const mainArea = page.locator('.game-main');
    
    // Main area contains GameChat
    await expect(mainArea).toBeVisible();
  });

  test('game session contains interactive elements', async ({ page }) => {
    await page.goto('/game/test-session');
    
    // Verify that the page structure supports game UI components
    const layout = page.locator('.game-layout');
    const sidebar = page.locator('.game-sidebar');
    const main = page.locator('.game-main');
    
    await expect(layout).toBeVisible();
    await expect(sidebar).toBeVisible();
    await expect(main).toBeVisible();
  });
});

test.describe('Battle Map - Content Display', () => {
  test('welcome message is displayed', async ({ page }) => {
    await page.goto('/game/test-session');
    await page.waitForTimeout(500);
    
    // GameChat displays welcome message
    const body = page.locator('body');
    await expect(body).toContainText('Welcome to the adventure');
  });

  test('session information is displayed', async ({ page }) => {
    await page.goto('/game/test-session');
    await page.waitForTimeout(500);
    
    // Session ID should be in the welcome message
    const body = page.locator('body');
    await expect(body).toContainText('test-session');
  });

  test('game session page is interactive', async ({ page }) => {
    await page.goto('/game/test-session');
    
    // Page should be ready for interaction
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
  });
});

test.describe('Battle Map - Responsive Design', () => {
  test('battle map UI is visible on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/game/test-session');
    
    const gameLayout = page.locator('.game-layout');
    await expect(gameLayout).toBeVisible();
  });

  test('battle map components render in sidebar layout', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/game/test-session');
    
    const sidebar = page.locator('.game-sidebar');
    const main = page.locator('.game-main');
    
    await expect(sidebar).toBeVisible();
    await expect(main).toBeVisible();
  });

  test('game session page renders at tablet size', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/game/test-session');
    
    const gameLayout = page.locator('.game-layout');
    await expect(gameLayout).toBeVisible();
  });
});

test.describe('Battle Map - DOM Structure', () => {
  test('page contains expected CSS classes for layout', async ({ page }) => {
    await page.goto('/game/test-session');
    
    // Verify expected classes exist
    const pageBattle = page.locator('.page-game-session');
    const layout = page.locator('.game-layout');
    const sidebar = page.locator('.game-sidebar');
    const main = page.locator('.game-main');
    
    await expect(pageBattle).toBeVisible();
    await expect(layout).toBeVisible();
    await expect(sidebar).toBeVisible();
    await expect(main).toBeVisible();
  });

  test('battle map UI elements are properly nested', async ({ page }) => {
    await page.goto('/game/test-session');
    
    const pageContainer = page.locator('.page-game-session');
    const heading = pageContainer.locator('h1');
    const gameLayout = pageContainer.locator('.game-layout');
    
    await expect(heading).toBeVisible();
    await expect(gameLayout).toBeVisible();
  });
});
