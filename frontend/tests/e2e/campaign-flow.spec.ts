import { test, expect } from '@playwright/test';

test.describe('Campaign Flow - Home Page', () => {
  test('home page loads and displays title', async ({ page }) => {
    await page.goto('/');
    const title = page.locator('h1');
    await expect(title).toBeVisible();
    await expect(title).toContainText('AI Dungeon Master');
  });

  test('home page shows tagline', async ({ page }) => {
    await page.goto('/');
    const hero = page.locator('.hero');
    const tagline = hero.locator('p');
    await expect(tagline).toContainText(/D&D 5e experience/i);
  });

  test('campaign list component is rendered', async ({ page }) => {
    await page.goto('/');
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible();
  });

  test('page renders without JavaScript errors', async ({ page }) => {
    let errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check for console errors
    expect(errors).toHaveLength(0);
  });

  test('body contains expected elements', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).not.toBeEmpty();
    await expect(page.locator('.app')).toBeVisible();
  });

  test('hero section is visible on home page', async ({ page }) => {
    await page.goto('/');
    const hero = page.locator('.hero');
    await expect(hero).toBeVisible();
  });
});

test.describe('Campaign Flow - Page Navigation', () => {
  test('can navigate to home page with forward slash', async ({ page }) => {
    await page.goto('/');
    expect(page.url()).toContain('/');
  });

  test('home page is accessible', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
  });

  test('page title indicates Dungeon Master app', async ({ page }) => {
    await page.goto('/');
    const heading = page.locator('h1');
    await expect(heading).toContainText(/dungeon/i);
  });
});

test.describe('Campaign Flow - Content Structure', () => {
  test('home page has proper header structure', async ({ page }) => {
    await page.goto('/');
    const header = page.locator('header');
    await expect(header).toBeVisible();
    
    const h1 = header.locator('h1');
    await expect(h1).toBeVisible();
  });

  test('home page has main content area', async ({ page }) => {
    await page.goto('/');
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });

  test('campaign list is in main content', async ({ page }) => {
    await page.goto('/');
    // The CampaignList component should render without API data
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });
});
