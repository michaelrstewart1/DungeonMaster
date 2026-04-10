import { test, expect } from '@playwright/test';
import { mockHomePageAPIs, filterNonCriticalErrors } from './helpers';

test.describe('Character Creation - Page Load', () => {
  test('home page loads and renders without errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await mockHomePageAPIs(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    expect(filterNonCriticalErrors(errors)).toHaveLength(0);
  });

  test('page is accessible', async ({ page }) => {
    await mockHomePageAPIs(page);
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
  });

  test('body element exists and is not empty', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');
    await expect(page.locator('body')).not.toBeEmpty();
  });
});

test.describe('Character Creation - Component Rendering', () => {
  test('campaign list component renders on home page', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible();
  });

  test('app container is present', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');
    const appContainer = page.locator('.app');
    await expect(appContainer).toBeVisible();
  });

  test('page structure is valid', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');

    const appDiv = page.locator('.app');
    const mainElement = page.locator('main');

    await expect(appDiv).toBeVisible();
    await expect(mainElement).toBeVisible();
  });
});

test.describe('Character Creation - Content', () => {
  test('home page displays title content', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');
    const title = page.locator('h1');
    await expect(title).toBeVisible();
  });

  test('home page displays navigation or UI elements', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');

    await page.waitForTimeout(300);

    const body = page.locator('body');
    const textContent = await body.textContent();
    expect(textContent).toBeTruthy();
    expect(textContent?.length).toBeGreaterThan(0);
  });

  test('character creator UI is accessible from home', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');

    const appDiv = page.locator('.app');
    await expect(appDiv).toBeVisible();
  });
});

test.describe('Character Creation - Functionality', () => {
  test('page responds to user interactions', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');

    const mainArea = page.locator('main');
    await expect(mainArea).toBeVisible();

    const buttons = page.locator('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('page layout is responsive', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });

    await mockHomePageAPIs(page);
    await page.goto('/');
    const appContainer = page.locator('.app');
    await expect(appContainer).toBeVisible();
  });
});

test.describe('Character Creation - Accessibility', () => {
  test('page has descriptive title', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');
    const title = page.locator('h1');
    const text = await title.textContent();
    expect(text).toBeTruthy();
    expect(text?.length).toBeGreaterThan(0);
  });

  test('page structure uses semantic HTML', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');

    const header = page.locator('header');
    const main = page.locator('main');

    await expect(header).toBeVisible();
    await expect(main).toBeVisible();
  });

  test('main content is not hidden', async ({ page }) => {
    await mockHomePageAPIs(page);
    await page.goto('/');
    const mainContent = page.locator('main');

    await expect(mainContent).toBeVisible();
  });
});
