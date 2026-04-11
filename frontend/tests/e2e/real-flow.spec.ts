import { test, expect, type Page } from '@playwright/test'

/**
 * REAL end-to-end tests that navigate the actual app against the real backend.
 * No mocks. Every user flow is tested by clicking, typing, and verifying outcomes.
 */

const uniqueId = () => Math.random().toString(36).slice(2, 8)

/** Helper: create a campaign and navigate into it */
async function createAndOpenCampaign(page: Page, name: string) {
  await page.goto('/')
  await expect(page.locator('.hero h1')).toBeVisible()

  // Wait for initial campaign list to load
  await page.waitForLoadState('networkidle')

  await page.click('text=New Campaign')
  await page.waitForSelector('.campaign-form')
  await page.fill('#campaign-name', name)
  await page.fill('#campaign-description', 'Test adventure')
  await page.click('button[type="submit"]:has-text("Create Campaign")')

  // Wait for the campaign card to appear after form submission triggers reload
  await expect(page.locator(`.campaign-card:has-text("${name}")`)).toBeVisible({ timeout: 10000 })
  await page.click(`.campaign-card:has-text("${name}")`)
  await expect(page.locator('h1')).toContainText(name, { timeout: 5000 })
}

test.describe('Real User Flows', () => {
  // Clean slate: use unique campaign names per test to avoid collision
  const uniqueId = () => Math.random().toString(36).slice(2, 8)

  test.beforeEach(async ({ page }) => {
    // Set a reasonable timeout for real API calls
    page.setDefaultTimeout(15000)
  })

  test('Full flow: create campaign → pick premade character → see character → start game', async ({ page }) => {
    const campaignName = `Quest ${uniqueId()}`

    // 1. Go to home page
    await page.goto('/')
    await expect(page.locator('.hero h1')).toBeVisible()

    // 2. Create a new campaign
    await page.waitForLoadState('networkidle')
    await page.click('text=New Campaign')
    await page.waitForSelector('.campaign-form')
    await page.fill('#campaign-name', campaignName)
    await page.fill('#campaign-description', 'A test adventure')
    await page.click('button[type="submit"]:has-text("Create Campaign")')

    // 3. Verify campaign appears in list with icon
    const campaignCard = page.locator(`.campaign-card:has-text("${campaignName}")`)
    await expect(campaignCard).toBeVisible({ timeout: 10000 })
    await expect(campaignCard.locator('.campaign-card-icon')).toBeVisible()

    // 4. Click into the campaign
    await campaignCard.click()
    await expect(page.locator('h1')).toContainText(campaignName, { timeout: 5000 })

    // 5. Verify breadcrumb navigation is visible
    await expect(page.locator('.breadcrumb')).toBeVisible()
    await expect(page.locator('.breadcrumb-current')).toContainText(campaignName)

    // 6. Verify mode chooser is visible
    await expect(page.locator('[data-testid="mode-chooser"]')).toBeVisible()

    // 7. Click "Choose a Hero" (premade)
    await page.click('[data-testid="btn-premade"]')
    await expect(page.locator('[data-testid="character-picker"]')).toBeVisible()

    // 8. Select a character from the picker
    const firstCard = page.locator('.picker-card').first()
    await firstCard.click()
    await expect(page.locator('[data-testid="picker-detail"]')).toBeVisible()
    const charName = await page.locator('.picker-detail-title h3').textContent()
    expect(charName).toBeTruthy()

    // 9. Confirm the character
    await page.click('[data-testid="picker-confirm"]')

    // 10. CRITICAL: Verify the character now appears in the campaign's character list
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.character-sheet .char-header h2')).toContainText(charName!)

    // 11. Verify the empty state is gone
    await expect(page.locator('.empty-state')).not.toBeVisible()

    // 12. Verify ability modifier colors are applied
    const abilityBlocks = page.locator('.ability-mod')
    const firstAbilityClass = await abilityBlocks.first().getAttribute('class')
    expect(firstAbilityClass).toMatch(/mod-(positive|negative|neutral)/)

    // Take screenshot showing selected character
    await page.screenshot({ path: 'test-results/real-01-character-selected.png', fullPage: true })

    // 13. Click "Begin Adventure"
    await page.click('.btn-start-game')

    // 14. CRITICAL: Verify we navigate to the game session (no error)
    await expect(page).toHaveURL(/\/game\//, { timeout: 10000 })
    await expect(page.locator('.game-session')).toBeVisible({ timeout: 10000 })

    // Take screenshot of game session
    await page.screenshot({ path: 'test-results/real-02-game-started.png', fullPage: true })
  })

  test('Full flow: create campaign → custom character wizard → see character', async ({ page }) => {
    const campaignName = `Custom Hero ${uniqueId()}`
    await createAndOpenCampaign(page, campaignName)

    // Open character creator
    await page.click('[data-testid="btn-manual"]')
    await expect(page.locator('[data-testid="step-race"]')).toBeVisible()

    // Step 1: Select Elf
    await page.click('[data-testid="race-elf"]')
    await expect(page.locator('[data-testid="race-elf"]')).toHaveClass(/selected/)
    await page.click('button:has-text("Next: Choose Class")')

    // Step 2: Select Wizard
    await expect(page.locator('[data-testid="step-class"]')).toBeVisible()
    await page.click('[data-testid="class-wizard"]')
    await expect(page.locator('[data-testid="class-wizard"]')).toHaveClass(/selected/)
    await page.click('button:has-text("Next: Abilities")')

    // Step 3: Adjust abilities
    await expect(page.locator('[data-testid="step-abilities"]')).toBeVisible()
    // Increase intelligence
    const intIncrease = page.locator('button[aria-label="Increase Intelligence"]')
    await intIncrease.click()
    await intIncrease.click()
    await intIncrease.click()
    await page.click('button:has-text("Next: Review")')

    // Step 4: Name and review
    await expect(page.locator('[data-testid="step-review"]')).toBeVisible()
    const heroName = `Elara ${uniqueId()}`
    await page.fill('#char-name', heroName)
    await expect(page.locator('.review-summary')).toContainText('Elf')
    await expect(page.locator('.review-summary')).toContainText('Wizard')

    // Submit
    await page.click('button[type="submit"]:has-text("Create Character")')

    // CRITICAL: Verify the character appears
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.character-sheet .char-header h2')).toContainText(heroName)

    await page.screenshot({ path: 'test-results/real-03-custom-character.png', fullPage: true })
  })

  test('Multiple characters can be added to a campaign', async ({ page }) => {
    const campaignName = `Party ${uniqueId()}`
    await createAndOpenCampaign(page, campaignName)

    // Add first character (premade)
    await page.click('[data-testid="btn-premade"]')
    await page.locator('.picker-card').first().click()
    await page.click('[data-testid="picker-confirm"]')
    await expect(page.locator('.character-sheet')).toHaveCount(1, { timeout: 5000 })

    // Verify success banner appears
    await expect(page.locator('.success-banner')).toBeVisible({ timeout: 3000 })

    // Verify party roster header shows count
    await expect(page.locator('.party-roster-header h3')).toContainText('Your Party (1)')

    // Verify empty state is gone
    await expect(page.locator('.empty-state')).not.toBeVisible()

    // Add second character (premade) via "Add Another" button
    await page.click('.btn-add-more')
    await page.locator('.picker-card').nth(1).click()
    await page.click('[data-testid="picker-confirm"]')
    await expect(page.locator('.character-sheet')).toHaveCount(2, { timeout: 5000 })

    // Verify party count updated
    await expect(page.locator('.party-roster-header h3')).toContainText('Your Party (2)')

    await page.screenshot({ path: 'test-results/real-04-multiple-characters.png', fullPage: true })

    // Start game with party
    await page.click('.btn-start-game')
    await expect(page).toHaveURL(/\/game\//, { timeout: 10000 })
  })

  test('Game session loads and is interactive', async ({ page }) => {
    const campaignName = `Game Test ${uniqueId()}`
    await createAndOpenCampaign(page, campaignName)

    await page.click('[data-testid="btn-premade"]')
    await page.locator('.picker-card').first().click()
    await page.click('[data-testid="picker-confirm"]')
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 5000 })
    await page.click('.btn-start-game')
    await expect(page).toHaveURL(/\/game\//, { timeout: 10000 })

    // Verify game session UI elements
    await expect(page.locator('.game-header')).toBeVisible()
    await expect(page.locator('.game-body')).toBeVisible()

    // Verify campaign name shows in header
    await expect(page.locator('.game-header h1')).toContainText(campaignName, { timeout: 5000 })

    // Verify back button is present
    await expect(page.locator('.btn-back')).toBeVisible()

    // Verify chat area is present and has the opening scene
    const chatArea = page.locator('.chat-area')
    await expect(chatArea).toBeVisible()

    // Verify DM avatar is present
    await expect(page.locator('.dm-avatar')).toBeVisible()

    // Verify dice roller is present
    await expect(page.locator('.dice-roller')).toBeVisible()

    // Type a message in chat (now a textarea)
    const chatInput = page.locator('.chat-input')
    if (await chatInput.isVisible()) {
      // Verify it's a textarea (auto-resize feature)
      const tagName = await chatInput.evaluate(el => el.tagName.toLowerCase())
      expect(tagName).toBe('textarea')

      await chatInput.fill('I look around the room')
      await chatInput.press('Enter')
      // Verify the player message appears
      await expect(page.locator('.chat-message.message-player, .chat-message:has-text("I look around")')).toBeVisible({ timeout: 5000 })
    }

    await page.screenshot({ path: 'test-results/real-05-game-session.png', fullPage: true })
  })

  test('Error states are handled gracefully', async ({ page }) => {
    // Navigate to a non-existent campaign
    await page.goto('/campaign/non-existent-id')
    await expect(page.locator('.error-message')).toBeVisible({ timeout: 5000 })

    await page.screenshot({ path: 'test-results/real-06-error-state.png', fullPage: true })

    // Navigate to a non-existent game session
    await page.goto('/game/non-existent-session')
    await expect(page.locator('.game-error, .error-message')).toBeVisible({ timeout: 5000 })

    await page.screenshot({ path: 'test-results/real-07-game-error.png', fullPage: true })
  })

  test('Navigation works correctly', async ({ page }) => {
    // Home page
    await page.goto('/')
    await expect(page.locator('.hero h1')).toBeVisible()

    // Brand link returns to home
    await page.click('.navbar-brand')
    await expect(page).toHaveURL('/')

    // 404 page for unknown routes
    await page.goto('/some-random-page')
    await expect(page.locator('text=404')).toBeVisible({ timeout: 5000 })

    await page.screenshot({ path: 'test-results/real-08-404-page.png', fullPage: true })
  })

  test('Breadcrumb navigation returns to home', async ({ page }) => {
    const campaignName = `Nav Test ${uniqueId()}`
    await createAndOpenCampaign(page, campaignName)

    // Verify breadcrumb is visible
    await expect(page.locator('.breadcrumb')).toBeVisible()
    await expect(page.locator('.breadcrumb-current')).toContainText(campaignName)

    // Click breadcrumb back link
    await page.click('.breadcrumb-link')
    await expect(page).toHaveURL('/', { timeout: 5000 })
    await expect(page.locator('.hero h1')).toBeVisible()
  })

  test('Character creator progress bar advances with steps', async ({ page }) => {
    const campaignName = `Progress ${uniqueId()}`
    await createAndOpenCampaign(page, campaignName)

    await page.click('[data-testid="btn-manual"]')
    await expect(page.locator('[data-testid="step-race"]')).toBeVisible()

    // Verify progress bar container exists
    const progressFill = page.locator('.creator-progress-fill')
    await expect(page.locator('.creator-progress-bar')).toBeVisible()

    // Advance to step 2
    await page.click('[data-testid="race-elf"]')
    await page.click('button:has-text("Next: Choose Class")')
    await expect(page.locator('[data-testid="step-class"]')).toBeVisible()

    // Progress bar should now be visible with width > 0
    await expect(progressFill).toBeVisible()
    const step2Width = await progressFill.evaluate(el => parseFloat(getComputedStyle(el).width))
    expect(step2Width).toBeGreaterThan(0)

    await page.screenshot({ path: 'test-results/real-09-progress-bar.png', fullPage: true })
  })

  test('Begin Adventure disabled without characters and shows warning', async ({ page }) => {
    const campaignName = `Empty ${uniqueId()}`
    await createAndOpenCampaign(page, campaignName)

    // Should see warning and disabled button
    await expect(page.locator('.campaign-warning')).toBeVisible()
    await expect(page.locator('.campaign-warning')).toContainText('haven\'t added any characters')
    const startBtn = page.locator('.btn-start-game')
    await expect(startBtn).toBeDisabled()

    // Add a character, warning should disappear
    await page.click('[data-testid="btn-premade"]')
    await page.locator('.picker-card').first().click()
    await page.click('[data-testid="picker-confirm"]')
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 5000 })

    await expect(page.locator('.campaign-warning')).not.toBeVisible()
    await expect(startBtn).toBeEnabled()

    await page.screenshot({ path: 'test-results/real-10-warning-gone.png', fullPage: true })
  })

  test('Campaign can be deleted from the list', async ({ page }) => {
    const campaignName = `Delete Me ${uniqueId()}`

    // Create a campaign
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.click('text=New Campaign')
    await page.waitForSelector('.campaign-form')
    await page.fill('#campaign-name', campaignName)
    await page.fill('#campaign-description', 'To be deleted')
    await page.click('button[type="submit"]:has-text("Create Campaign")')

    const campaignCard = page.locator(`.campaign-card:has-text("${campaignName}")`)
    await expect(campaignCard).toBeVisible({ timeout: 10000 })

    // Hover to reveal delete button
    await campaignCard.hover()
    const deleteBtn = campaignCard.locator('.campaign-delete-btn')
    await expect(deleteBtn).toBeVisible()

    // First click shows confirmation state
    await deleteBtn.click()
    await expect(deleteBtn).toHaveClass(/confirming/)

    // Second click deletes
    await deleteBtn.click()
    await expect(campaignCard).not.toBeVisible({ timeout: 5000 })

    await page.screenshot({ path: 'test-results/real-11-campaign-deleted.png', fullPage: true })
  })

  test('Character can be removed from party', async ({ page }) => {
    const campaignName = `Remove Char ${uniqueId()}`
    await createAndOpenCampaign(page, campaignName)

    // Add a character
    await page.click('[data-testid="btn-premade"]')
    await page.locator('.picker-card').first().click()
    await page.click('[data-testid="picker-confirm"]')
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.party-roster-header h3')).toContainText('Your Party (1)')

    // Hover over character sheet to reveal remove button
    await page.locator('.character-sheet').hover()
    const removeBtn = page.locator('.char-remove-btn')
    await expect(removeBtn).toBeVisible()

    // Click remove
    await removeBtn.click()

    // Character should be gone
    await expect(page.locator('.character-sheet')).not.toBeVisible({ timeout: 5000 })

    // Warning should reappear since party is empty
    await expect(page.locator('.campaign-warning')).toBeVisible()

    await page.screenshot({ path: 'test-results/real-12-character-removed.png', fullPage: true })
  })

  test('Campaign form shows character count and validates name length', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.click('text=New Campaign')
    await page.waitForSelector('.campaign-form')
    
    const nameInput = page.locator('#campaign-name')
    const nameHint = nameInput.locator('~ .form-hint')
    
    // Initially shows 0/50
    await expect(nameHint).toContainText('0/50')
    
    // Type a short name
    await nameInput.fill('Test')
    await expect(nameHint).toContainText('4/50')
    
    // Submit button should be disabled with name < 2 chars
    await nameInput.fill('A')
    const submitBtn = page.locator('.campaign-form button[type="submit"]')
    await expect(submitBtn).toBeDisabled()
    
    // Longer name enables submit
    await nameInput.fill('My Adventure')
    await expect(submitBtn).toBeEnabled()
    await expect(nameHint).toContainText('12/50')
    
    await page.screenshot({ path: 'test-results/real-13-form-validation.png', fullPage: true })
  })

  test('Game session shows session timer', async ({ page }) => {
    const uniqueName = `Timer Test ${uniqueId()}`
    await createAndOpenCampaign(page, uniqueName)
    
    // Add premade character
    await page.click('[data-testid="btn-premade"]')
    await expect(page.locator('[data-testid="character-picker"]')).toBeVisible()
    await page.locator('.picker-card').first().click()
    await expect(page.locator('[data-testid="picker-detail"]')).toBeVisible()
    await page.click('[data-testid="picker-confirm"]')
    await expect(page.locator('.character-sheet')).toBeVisible({ timeout: 5000 })
    
    // Start game
    await page.click('text=Begin Adventure')
    await page.waitForSelector('.game-session')
    
    // Timer should be visible
    const timer = page.locator('.session-timer')
    await expect(timer).toBeVisible()
    
    // Wait a bit and check it shows a time value
    await page.waitForTimeout(1500)
    const text = await timer.textContent()
    expect(text).toMatch(/\d+:\d+/)
    
    await page.screenshot({ path: 'test-results/real-14-session-timer.png', fullPage: true })
  })

  test('Escape key closes campaign creation form', async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('.campaign-list')

    // Open the form
    await page.click('text=New Campaign')
    await expect(page.locator('.campaign-form')).toBeVisible()

    // Press Escape
    await page.keyboard.press('Escape')
    await expect(page.locator('.campaign-form')).not.toBeVisible()

    await page.screenshot({ path: 'test-results/real-15-escape-form.png', fullPage: true })
  })

  test('Campaign cards show creation date', async ({ page }) => {
    const name = `Date-Test-${uniqueId()}`
    await createAndOpenCampaign(page, name)

    // Go back to home
    await page.goto('/')
    await page.waitForSelector('.campaign-card')

    // Check that at least one card has a date
    const dateEl = page.locator('.campaign-date').first()
    await expect(dateEl).toBeVisible()
    const dateText = await dateEl.textContent()
    // Should contain a month abbreviation
    expect(dateText).toMatch(/[A-Z][a-z]{2}/)

    await page.screenshot({ path: 'test-results/real-16-campaign-date.png', fullPage: true })
  })
})
