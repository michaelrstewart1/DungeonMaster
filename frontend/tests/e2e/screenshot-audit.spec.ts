import { test } from '@playwright/test'

const BASE = process.env.E2E_BASE_URL || 'http://localhost:5173'

test('Screenshot all pages', async ({ page }) => {
  test.setTimeout(60000)

  // Home page
  await page.goto(BASE)
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: 'test-results/screenshot-home.png', fullPage: true })

  // Create campaign via the form
  const campName = `ScreenshotAudit_${Date.now()}`
  await page.click('text=New Campaign')
  await page.waitForSelector('.campaign-form')
  await page.fill('#campaign-name', campName)
  await page.fill('#campaign-description', 'Visual audit')
  await page.click('button[type="submit"]:has-text("Create Campaign")')

  // Wait for card and click it
  await page.locator(`.campaign-card:has-text("${campName}")`).click()
  await page.waitForURL(/\/campaign\//)
  await page.waitForSelector('.page-campaign-detail header h1', { timeout: 10000 })
  await page.waitForTimeout(500)
  await page.screenshot({ path: 'test-results/screenshot-campaign-detail.png', fullPage: true })

  // Character picker
  await page.click('[data-testid="btn-premade"]')
  await page.waitForSelector('.character-picker')
  await page.screenshot({ path: 'test-results/screenshot-character-picker.png', fullPage: true })

  // Select a character
  await page.locator('.picker-card').first().click()
  await page.screenshot({ path: 'test-results/screenshot-character-selected.png', fullPage: true })

  // Accept character
  const acceptBtn = page.locator('button:has-text("Accept")')
  if (await acceptBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await acceptBtn.click()
    await page.waitForTimeout(1000)
  }
  await page.screenshot({ path: 'test-results/screenshot-character-added.png', fullPage: true })

  // Start game
  await page.click('.btn-start-game')
  await page.waitForURL(/\/game\//)
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(2000)
  await page.screenshot({ path: 'test-results/screenshot-game-session.png', fullPage: true })
})
