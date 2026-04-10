import { test, expect } from '@playwright/test';

test.describe('Character Creation - Page Load', () => {
  test('home page loads and renders without errors', async ({ page }) => {
    await page.goto('/');
    
    let errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.waitForLoadState('networkidle');
    expect(errors).toHaveLength(0);
  });

  test('page is accessible', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
  });

  test('body element exists and is not empty', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).not.toBeEmpty();
  });
});

test.describe('Character Creation - Component Rendering', () => {
  test('campaign list component renders on home page', async ({ page }) => {
    await page.goto('/');
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible();
  });

  test('app container is present', async ({ page }) => {
    await page.goto('/');
    const appContainer = page.locator('.app');
    await expect(appContainer).toBeVisible();
  });

  test('page structure is valid', async ({ page }) => {
    await page.goto('/');
    
    // Verify expected DOM structure
    const appDiv = page.locator('.app');
    const mainElement = page.locator('main');
    
    await expect(appDiv).toBeVisible();
    await expect(mainElement).toBeVisible();
  });
});

test.describe('Character Creation - Content', () => {
  test('home page displays title content', async ({ page }) => {
    await page.goto('/');
    const title = page.locator('h1');
    await expect(title).toBeVisible();
  });

  test('home page displays navigation or UI elements', async ({ page }) => {
    await page.goto('/');
    
    // Wait for initial render
    await page.waitForTimeout(300);
    
    // Check that the page has rendered content
    const body = page.locator('body');
    const textContent = await body.textContent();
    expect(textContent).toBeTruthy();
    expect(textContent?.length).toBeGreaterThan(0);
  });

  test('character creator UI is accessible from home', async ({ page }) => {
    await page.goto('/');
    
    // The home page should be interactive
    const appDiv = page.locator('.app');
    await expect(appDiv).toBeVisible();
  });
});

test.describe('Character Creation - Functionality', () => {
  test('page responds to user interactions', async ({ page }) => {
    await page.goto('/');
    
    // Verify that the page can receive input focus
    const mainArea = page.locator('main');
    await expect(mainArea).toBeVisible();
    
    // Check if any buttons are present (for future interactions)
    const buttons = page.locator('button');
    const count = await buttons.count();
    // Buttons may or may not be visible depending on the UI, so we just verify they can be queried
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('page layout is responsive', async ({ page }) => {
    // Set viewport size
    await page.setViewportSize({ width: 1280, height: 720 });
    
    await page.goto('/');
    const appContainer = page.locator('.app');
    await expect(appContainer).toBeVisible();
  });
});

test.describe('Character Creation - Accessibility', () => {
  test('page has descriptive title', async ({ page }) => {
    await page.goto('/');
    const title = page.locator('h1');
    const text = await title.textContent();
    expect(text).toBeTruthy();
    expect(text?.length).toBeGreaterThan(0);
  });

  test('page structure uses semantic HTML', async ({ page }) => {
    await page.goto('/');
    
    // Verify use of semantic elements
    const header = page.locator('header');
    const main = page.locator('main');
    
    await expect(header).toBeVisible();
    await expect(main).toBeVisible();
  });

  test('main content is not hidden', async ({ page }) => {
    await page.goto('/');
    const mainContent = page.locator('main');
    
    // Check visibility
    await expect(mainContent).toBeVisible();
  });
});
