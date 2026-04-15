import { test, expect, type Page } from '@playwright/test'

/**
 * OVERNIGHT PLAYTEST — Comprehensive game flow test against the live server.
 * Screenshots every step so we can visually inspect the UI.
 * Run with: E2E_BASE_URL=http://192.168.1.94 npx playwright test tests/e2e/overnight-playtest.spec.ts --reporter=list
 */

const SCREENSHOT_DIR = 'test-results/overnight'

async function screenshot(page: Page, name: string) {
  await page.screenshot({ path: `${SCREENSHOT_DIR}/${name}.png`, fullPage: false })
}

async function screenshotFull(page: Page, name: string) {
  await page.screenshot({ path: `${SCREENSHOT_DIR}/${name}.png`, fullPage: true })
}

test.describe('Overnight Playtest', () => {
  test.setTimeout(120_000) // 2 minutes per test

  test('01 — Home page loads with hero and featured campaigns', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Hero section
    await expect(page.locator('.hero h1')).toBeVisible({ timeout: 10000 })
    await screenshot(page, '01-home-hero')
    
    // Featured campaigns section
    const featured = page.locator('.featured-campaigns')
    if (await featured.isVisible()) {
      await featured.scrollIntoViewIfNeeded()
      await screenshot(page, '01-home-featured')
    }
    
    // Full page
    await screenshotFull(page, '01-home-full')
  })

  test('02 — Launch premade campaign (Stormspire)', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Click the first featured campaign
    const featuredCard = page.locator('.featured-card').first()
    await expect(featuredCard).toBeVisible({ timeout: 10000 })
    await featuredCard.click()
    
    // Should navigate to campaign detail
    await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
    await page.waitForLoadState('networkidle')
    await screenshot(page, '02-campaign-detail-top')
    
    // Check hero banner if present
    const heroBanner = page.locator('.campaign-hero-banner')
    if (await heroBanner.isVisible()) {
      await screenshot(page, '02-campaign-hero-banner')
    }
    
    // Full page
    await screenshotFull(page, '02-campaign-detail-full')
  })

  test('03 — Pick a premade character', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Launch a premade campaign
    const featuredCard = page.locator('.featured-card').first()
    await featuredCard.click()
    await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
    await page.waitForLoadState('networkidle')
    
    // Choose a Hero
    const premadeBtn = page.locator('[data-testid="btn-premade"]')
    await expect(premadeBtn).toBeVisible({ timeout: 10000 })
    await premadeBtn.click()
    
    // Character picker should appear
    await expect(page.locator('[data-testid="character-picker"]')).toBeVisible({ timeout: 10000 })
    await screenshot(page, '03-character-picker')
    
    // Click first character
    const firstCard = page.locator('.picker-card').first()
    await firstCard.click()
    await expect(page.locator('[data-testid="picker-detail"]')).toBeVisible()
    await screenshot(page, '03-character-detail')
    
    // Confirm — wait for the API response before checking UI
    const [confirmResponse] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/characters') && resp.request().method() === 'POST', { timeout: 15000 }),
      page.click('[data-testid="picker-confirm"]'),
    ])
    expect(confirmResponse.status()).toBeLessThan(400)

    // Should see character sheet (picker closes, characters reload)
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 15000 })
    await screenshot(page, '03-character-added')
    await screenshotFull(page, '03-campaign-with-character-full')
  })

  test('04 — Start game session and play', async ({ page }) => {
    test.setTimeout(120_000) // 2 min — Ollama responses can be slow
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Launch a premade campaign
    const featuredCard = page.locator('.featured-card').first()
    await featuredCard.click()
    await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
    await page.waitForLoadState('networkidle')
    
    // Add a character first
    const premadeBtn = page.locator('[data-testid="btn-premade"]')
    await expect(premadeBtn).toBeVisible({ timeout: 10000 })
    await premadeBtn.click()
    await expect(page.locator('[data-testid="character-picker"]')).toBeVisible({ timeout: 10000 })
    await page.locator('.picker-card').first().click()
    await expect(page.locator('[data-testid="picker-detail"]')).toBeVisible()
    await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/characters') && resp.request().method() === 'POST', { timeout: 15000 }),
      page.click('[data-testid="picker-confirm"]'),
    ])
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 15000 })
    
    // Click Begin Adventure
    const startBtn = page.locator('.btn-start-game')
    await expect(startBtn).toBeEnabled({ timeout: 5000 })
    await startBtn.click()
    
    // Should navigate to game session
    await expect(page).toHaveURL(/\/game\//, { timeout: 15000 })
    
    // Wait for game UI to load (greeting has 8s client timeout)
    await screenshot(page, '04-game-session-initial')
    
    // Check for error boundary
    const errorBoundary = page.locator('text=Something went wrong')
    if (await errorBoundary.isVisible()) {
      await screenshot(page, '04-ERROR-game-crashed')
      const errorText = await page.locator('.error-details, .error-message').textContent().catch(() => 'no details')
      console.error('GAME CRASHED:', errorText)
      return
    }
    
    // Wait for chat input to appear (greeting loaded or timed out)
    const actionInput = page.locator('textarea.chat-input')
    await expect(actionInput).toBeVisible({ timeout: 15000 })
    await screenshot(page, '04-game-session-loaded')
    
    // Wait for AI greeting to upgrade (gives Ollama time under load)
    const dmMessage = page.locator('.dm-message').first()
    await dmMessage.waitFor({ timeout: 5000 }).catch(() => {})
    // Wait a bit for the async greeting replacement
    await page.waitForTimeout(8000)
    
    // Check map area
    const mapArea = page.locator('.map-area')
    if (await mapArea.isVisible()) {
      await screenshot(page, '04-map-area')
    }
    
    // Check chat area
    const chatArea = page.locator('.chat-area')
    if (await chatArea.isVisible()) {
      await screenshot(page, '04-chat-area')
    }
    
    // Take greeting screenshot
    await screenshot(page, '04-after-greeting')
    
    // Type an action
    if (await actionInput.isVisible()) {
      await actionInput.fill('I look around the room and check for traps')
      await screenshot(page, '04-action-typed')
      
      // Submit the action
      const sendBtn = page.locator('.chat-submit')
      if (await sendBtn.isVisible()) {
        await sendBtn.click()
      } else {
        await actionInput.press('Enter')
      }
      
      // Wait for response
      await page.waitForTimeout(10000)
      await screenshot(page, '04-after-action-response')
    }
    
    // Check sidebars
    const leftSidebar = page.locator('.game-sidebar-left')
    if (await leftSidebar.isVisible()) {
      await screenshot(page, '04-left-sidebar')
    }
    
    const rightSidebar = page.locator('.game-sidebar-right')
    if (await rightSidebar.isVisible()) {
      await screenshot(page, '04-right-sidebar')
    }
    
    // Full page screenshot
    await screenshotFull(page, '04-game-session-full')
  })

  test('05 — Custom character creation wizard', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Create a custom campaign
    await page.click('text=New Campaign')
    await page.waitForSelector('.campaign-form', { timeout: 10000 })
    const name = `Playtest ${Date.now()}`
    await page.fill('#campaign-name', name)
    await page.fill('#campaign-description', 'Overnight playtest campaign')
    await page.click('button[type="submit"]:has-text("Create Campaign")')
    
    // Navigate to it
    const card = page.locator(`.campaign-card:has-text("${name}")`)
    await expect(card).toBeVisible({ timeout: 10000 })
    await card.click()
    await expect(page).toHaveURL(/\/campaign\//, { timeout: 10000 })
    
    // Open custom character creator
    await page.click('[data-testid="btn-manual"]')
    const stepEl = page.locator('[data-testid="step-race"]')
    await expect(stepEl).toBeVisible({ timeout: 10000 })
    await stepEl.scrollIntoViewIfNeeded()
    await page.waitForTimeout(800) // Wait for card entrance animations
    await screenshot(page, '05-wizard-step1-race')
    
    // Pick a race
    await page.click('[data-testid="race-elf"]')
    await page.click('button:has-text("Next: Choose Class")')
    await expect(page.locator('[data-testid="step-class"]')).toBeVisible()
    await page.locator('[data-testid="step-class"]').scrollIntoViewIfNeeded()
    await page.waitForTimeout(800)
    await screenshot(page, '05-wizard-step2-class')
    
    // Pick a class
    await page.click('[data-testid="class-wizard"]')
    await page.click('button:has-text("Next: Background")')
    await expect(page.locator('[data-testid="step-background"]')).toBeVisible()
    await page.locator('[data-testid="step-background"]').scrollIntoViewIfNeeded()
    await page.waitForTimeout(800)
    await screenshot(page, '05-wizard-step2b-background')
    
    // Pick a background
    await page.locator('.background-card').first().click()
    await page.click('button:has-text("Next: Abilities")')
    await expect(page.locator('[data-testid="step-abilities"]')).toBeVisible()
    await page.locator('[data-testid="step-abilities"]').scrollIntoViewIfNeeded()
    await page.waitForTimeout(500)
    await screenshot(page, '05-wizard-step3-abilities')
    
    // Step 3: Abilities — bump a few scores via point buy
    const plusBtns = page.locator('.ability-card .ability-btn:has-text("+")')
    const btnCount = await plusBtns.count()
    if (btnCount >= 6) {
      // Bump STR, DEX, CON, INT, WIS, CHA each by 2 clicks (8→10)
      for (let i = 0; i < 6; i++) {
        await plusBtns.nth(i).click()
        await plusBtns.nth(i).click()
      }
    }
    await screenshot(page, '05-wizard-step3b-abilities-assigned')
    
    await page.click('button:has-text("Next: Skills")')
    await expect(page.locator('[data-testid="step-skills"]')).toBeVisible()
    await page.locator('[data-testid="step-skills"]').scrollIntoViewIfNeeded()
    await page.waitForTimeout(500)
    await screenshot(page, '05-wizard-step4-skills')
    
    // Step 4: Skills — just proceed
    await page.click('button:has-text("Next: Equipment")')
    await expect(page.locator('[data-testid="step-equipment"]')).toBeVisible()
    await page.locator('[data-testid="step-equipment"]').scrollIntoViewIfNeeded()
    await page.waitForTimeout(500)
    await screenshot(page, '05-wizard-step5-equipment')
    
    // Step 5: Equipment — Wizard is a spellcaster so next is Spells
    await page.click('button:has-text("Next: Spells")')
    await expect(page.locator('[data-testid="step-spells"]')).toBeVisible()
    await page.locator('[data-testid="step-spells"]').scrollIntoViewIfNeeded()
    await page.waitForTimeout(500)
    await screenshot(page, '05-wizard-step5b-spells')
    
    // Step 6: Spells — just proceed
    await page.click('button:has-text("Next: Details")')
    await expect(page.locator('[data-testid="step-details"]')).toBeVisible()
    await page.locator('[data-testid="step-details"]').scrollIntoViewIfNeeded()
    await page.waitForTimeout(500)
    await screenshot(page, '05-wizard-step6-details')
    
    // Fill character name
    const nameInput = page.locator('#char-name, [data-testid="char-name"], input[placeholder*="name" i]')
    if (await nameInput.isVisible()) {
      await nameInput.fill('Elara Nightwhisper')
    }
    await screenshot(page, '05-wizard-step6-details-filled')
    
    // Next: Review
    await page.click('button:has-text("Next: Review")')
    await expect(page.locator('[data-testid="step-review"]')).toBeVisible()
    await page.locator('[data-testid="step-review"]').scrollIntoViewIfNeeded()
    await page.waitForTimeout(800)
    await screenshot(page, '05-wizard-step7-review')
    
    await screenshotFull(page, '05-wizard-full')
  })

  test('06 — Campaign settings modal', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Launch premade campaign
    const featuredCard = page.locator('.featured-card').first()
    await featuredCard.click()
    await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
    await page.waitForLoadState('networkidle')
    
    // Open settings
    const settingsBtn = page.locator('[data-testid="btn-settings"]')
    await expect(settingsBtn).toBeVisible({ timeout: 10000 })
    await settingsBtn.click()
    
    // Settings modal
    await page.waitForTimeout(500)
    await screenshot(page, '06-settings-modal')
    await screenshotFull(page, '06-settings-full')
  })

  test('07 — Navigate back home from campaign detail', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Launch premade campaign
    const featuredCard = page.locator('.featured-card').first()
    await featuredCard.click()
    await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
    await page.waitForLoadState('networkidle')
    
    // Click breadcrumb back
    await page.click('.breadcrumb-link')
    await expect(page).toHaveURL('/', { timeout: 10000 })
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.hero, .featured-campaigns')).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500) // Let background slideshow and animations settle
    await screenshot(page, '07-back-home')
  })

  test('08 — Multiple characters in a campaign', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Launch premade campaign
    const featuredCard = page.locator('.featured-card').first()
    await featuredCard.click()
    await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
    await page.waitForLoadState('networkidle')
    
    // Add first character
    await page.click('[data-testid="btn-premade"]')
    await expect(page.locator('[data-testid="character-picker"]')).toBeVisible({ timeout: 10000 })
    await page.locator('.picker-card').first().click()
    await expect(page.locator('[data-testid="picker-detail"]')).toBeVisible()
    await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/characters') && resp.request().method() === 'POST', { timeout: 15000 }),
      page.click('[data-testid="picker-confirm"]'),
    ])
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 15000 })
    
    // Add second character
    const addBtn = page.locator('.party-tray-add, button:has-text("+ Add")')
    if (await addBtn.isVisible()) {
      await addBtn.click()
      await expect(page.locator('[data-testid="character-picker"]')).toBeVisible({ timeout: 10000 })
      await page.locator('.picker-card').nth(1).click()
      await expect(page.locator('[data-testid="picker-detail"]')).toBeVisible()
      await Promise.all([
        page.waitForResponse(resp => resp.url().includes('/api/characters') && resp.request().method() === 'POST', { timeout: 15000 }),
        page.click('[data-testid="picker-confirm"]'),
      ])
      await page.waitForTimeout(2000)
    }
    
    await screenshot(page, '08-multiple-characters')
    await screenshotFull(page, '08-party-full')
  })

  test('09 — Game session with multiple interactions', async ({ page }) => {
    test.setTimeout(300_000) // 5 min — Ollama can be slow under concurrent load
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Launch premade campaign
    const featuredCard = page.locator('.featured-card').first()
    await featuredCard.click()
    await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
    await page.waitForLoadState('networkidle')
    
    // Add character
    await page.click('[data-testid="btn-premade"]')
    await expect(page.locator('[data-testid="character-picker"]')).toBeVisible({ timeout: 10000 })
    await page.locator('.picker-card').first().click()
    await expect(page.locator('[data-testid="picker-detail"]')).toBeVisible()
    await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/characters') && resp.request().method() === 'POST', { timeout: 15000 }),
      page.click('[data-testid="picker-confirm"]'),
    ])
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 15000 })
    
    // Start game
    await page.locator('.btn-start-game').click()
    await expect(page).toHaveURL(/\/game\//, { timeout: 15000 })
    
    // Wait for game to load (greeting has 8s client timeout)
    const chatInput = page.locator('textarea.chat-input')
    await expect(chatInput).toBeVisible({ timeout: 15000 })
    
    // Check for error
    const errorBoundary = page.locator('text=Something went wrong')
    if (await errorBoundary.isVisible()) {
      await screenshot(page, '09-ERROR')
      return
    }
    
    // Wait for the AI greeting to arrive (may get >1 DM msg if greeting + scene intro)
    await expect(page.locator('.message-dm:not(.typing-message)')).not.toHaveCount(0, { timeout: 60000 })
    await screenshot(page, '09-game-start')
    
    // Send multiple actions
    const actions = [
      'I examine my surroundings carefully',
      'I check my inventory',
      'I move toward the nearest door',
    ]
    
    for (let i = 0; i < actions.length; i++) {
      const actionInput = page.locator('textarea.chat-input')
      await expect(actionInput).toBeEnabled({ timeout: 60000 })
      
      // Count existing DM messages before sending action
      const dmMessagesBefore = await page.locator('.message-dm:not(.typing-message)').count()
      
      await actionInput.fill(actions[i])
      const sendBtn = page.locator('.chat-submit')
      if (await sendBtn.isVisible()) {
        await sendBtn.click()
      } else {
        await actionInput.press('Enter')
      }
      // Wait for a NEW DM message to appear (more reliable than disabled/enabled race)
      await expect(page.locator('.message-dm:not(.typing-message)')).toHaveCount(dmMessagesBefore + 1, { timeout: 90000 })
      await page.waitForTimeout(500) // Brief pause for render
      await screenshot(page, `09-action-${i + 1}-response`)
    }
    
    await screenshotFull(page, '09-game-multi-turn-full')
  })

  test('10 — Responsive check at tablet width', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    
    // Home page
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await screenshot(page, '10-tablet-home')
    
    // Campaign detail
    const featuredCard = page.locator('.featured-card').first()
    if (await featuredCard.isVisible()) {
      await featuredCard.click()
      await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
      await page.waitForLoadState('networkidle')
      await page.waitForSelector('.campaign-hero-banner, .page-campaign-detail header h1, .campaign-detail-header', { timeout: 10000 }).catch(() => {})
      await page.waitForTimeout(500)
      await screenshot(page, '10-tablet-campaign')
    }
  })

  test('11 — Responsive check at mobile width', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    
    // Home page
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await screenshot(page, '11-mobile-home')
    
    // Campaign detail
    const featuredCard = page.locator('.featured-card').first()
    if (await featuredCard.isVisible()) {
      await featuredCard.click()
      await expect(page).toHaveURL(/\/campaign\//, { timeout: 15000 })
      await page.waitForLoadState('networkidle')
      // Wait for campaign content to actually render
      await page.waitForSelector('.campaign-hero-banner, .page-campaign-detail header h1, .campaign-detail-header', { timeout: 10000 }).catch(() => {})
      await page.waitForTimeout(500)
      await screenshot(page, '11-mobile-campaign')
    }
  })

})
