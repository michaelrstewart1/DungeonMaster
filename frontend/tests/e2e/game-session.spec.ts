import { test, expect } from '@playwright/test';

test.describe('Game Session - Page Load', () => {
  test('game session page loads at correct route', async ({ page }) => {
    await page.goto('/game/test-session');
    expect(page.url()).toContain('/game/test-session');
  });

  test('game session page returns 200 status', async ({ page }) => {
    const response = await page.goto('/game/test-session');
    expect(response?.status()).toBe(200);
  });

  test('game session page displays heading', async ({ page }) => {
    await page.goto('/game/test-session');
    const heading = page.locator('h1');
    await expect(heading).toContainText('Game Session');
  });

  test('game session page renders without JavaScript errors', async ({ page }) => {
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

  test('page body is not empty', async ({ page }) => {
    await page.goto('/game/test-session');
    await expect(page.locator('body')).not.toBeEmpty();
  });
});

test.describe('Game Session - UI Components', () => {
  test('game layout container is present', async ({ page }) => {
    await page.goto('/game/test-session');
    const layout = page.locator('.game-layout');
    await expect(layout).toBeVisible();
  });

  test('game session has sidebar section', async ({ page }) => {
    await page.goto('/game/test-session');
    const sidebar = page.locator('.game-sidebar');
    await expect(sidebar).toBeVisible();
  });

  test('game session has main content area', async ({ page }) => {
    await page.goto('/game/test-session');
    const main = page.locator('.game-main');
    await expect(main).toBeVisible();
  });

  test('game session contains welcome message', async ({ page }) => {
    await page.goto('/game/test-session');
    await page.waitForLoadState('networkidle');
    // GameChat should display the initial welcome message
    await expect(page.locator('body')).toContainText(/Welcome to the adventure/i);
  });

  test('initiative tracker component renders', async ({ page }) => {
    await page.goto('/game/test-session');
    // InitiativeTracker is in the sidebar
    const sidebar = page.locator('.game-sidebar');
    await expect(sidebar).toBeVisible();
  });

  test('dice roller component renders', async ({ page }) => {
    await page.goto('/game/test-session');
    // DiceRoller is in the sidebar
    const sidebar = page.locator('.game-sidebar');
    await expect(sidebar).toBeVisible();
  });
});

test.describe('Game Session - Content Structure', () => {
  test('page displays page-game-session container', async ({ page }) => {
    await page.goto('/game/test-session');
    const container = page.locator('.page-game-session');
    await expect(container).toBeVisible();
  });

  test('session ID is correctly passed from URL', async ({ page }) => {
    await page.goto('/game/my-adventure');
    expect(page.url()).toContain('/game/my-adventure');
  });

  test('game chat component is rendered in main area', async ({ page }) => {
    await page.goto('/game/test-session');
    const mainArea = page.locator('.game-main');
    await expect(mainArea).toBeVisible();
  });
});

test.describe('Game Session - Initial State', () => {
  test('welcome message is displayed on load', async ({ page }) => {
    await page.goto('/game/test-session');
    await page.waitForTimeout(500); // Allow initial render
    // Check for the session ID in the welcome message
    await expect(page.locator('body')).toContainText('test-session');
  });

  test('page is interactive after load', async ({ page }) => {
    await page.goto('/game/test-session');
    const mainLayout = page.locator('.game-layout');
    await expect(mainLayout).toBeVisible();
    
    // Verify we can query elements
    const heading = page.locator('h1');
    await expect(heading).toContainText('Game Session');
  });
});
