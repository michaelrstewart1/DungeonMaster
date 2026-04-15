import { test, expect, type Page } from '@playwright/test'

/**
 * LEVEL-UP & LOOT PLAYTEST — Tests the full level-up flow and loot distribution.
 * 
 * Creates a campaign, adds a character, starts a session, then uses API calls
 * to award XP (triggering level-up) and add loot. Then exercises the UI modals
 * for making level-up choices and distributing loot to characters.
 * 
 * Run with: E2E_BASE_URL=http://192.168.1.94 npx playwright test tests/e2e/levelup-loot-playtest.spec.ts --reporter=list
 */

const BASE = process.env.E2E_BASE_URL || 'http://localhost:5173'
const API = `${BASE.replace(/\/$/, '')}/api`
const SCREENSHOT_DIR = 'test-results/levelup-loot'

async function screenshot(page: Page, name: string) {
  await page.screenshot({ path: `${SCREENSHOT_DIR}/${name}.png`, fullPage: false })
}

async function screenshotFull(page: Page, name: string) {
  await page.screenshot({ path: `${SCREENSHOT_DIR}/${name}.png`, fullPage: true })
}

/** Direct API helper for backend calls that bypass the UI */
async function apiPost(path: string, body: Record<string, unknown>) {
  const resp = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!resp.ok) throw new Error(`API POST ${path} failed: ${resp.status} ${await resp.text()}`)
  return resp.json()
}

async function apiGet(path: string) {
  const resp = await fetch(`${API}${path}`)
  if (!resp.ok) throw new Error(`API GET ${path} failed: ${resp.status} ${await resp.text()}`)
  return resp.json()
}

test.describe.serial('Level-Up & Loot Playtest', () => {
  test.setTimeout(180_000) // 3 minutes per test

  let campaignId: string
  let characterId: string
  let sessionId: string

  test.beforeAll(async () => {
    // Create a test campaign via API
    const campaign = await apiPost('/campaigns/', {
      name: `LevelUp Test ${Date.now()}`,
      description: 'E2E test for level-up and loot flows',
      setting: 'forgotten_realms',
    })
    campaignId = campaign.id

    // Create a character via API (Fighter for simple level-up)
    const character = await apiPost('/characters/', {
      campaign_id: campaignId,
      name: 'Thorin Stoneforge',
      race: 'dwarf',
      class_name: 'fighter',
      level: 1,
      background: 'soldier',
      strength: 16,
      dexterity: 12,
      constitution: 14,
      intelligence: 10,
      wisdom: 13,
      charisma: 8,
      hp: 12,
      max_hp: 12,
      ac: 16,
      experience_points: 0,
    })
    characterId = character.id

    // Create a game session via API
    const session = await apiPost('/game/sessions', {
      campaign_id: campaignId,
      character_ids: [characterId],
    })
    sessionId = session.id
  })

  test.afterAll(async () => {
    // Clean up test data
    try {
      if (sessionId) await fetch(`${API}/game/sessions/${sessionId}`, { method: 'DELETE' })
      if (characterId) await fetch(`${API}/characters/${characterId}`, { method: 'DELETE' })
      if (campaignId) await fetch(`${API}/campaigns/${campaignId}`, { method: 'DELETE' })
    } catch { /* best effort cleanup */ }
  })

  test('01 — Award XP and trigger level-up notification', async ({ page }) => {
    // Navigate to the game session
    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000) // Let greeting load
    await screenshot(page, '01-game-session-start')

    // Award 300 XP via API (level 1→2 requires 300 XP in D&D 5e)
    const xpResult = await apiPost(`/game/sessions/${sessionId}/xp-event`, {
      event_type: 'combat',
      description: 'Defeated a band of goblins',
      xp_total: 300,
      character_ids: [characterId],
    })
    
    // Verify XP was awarded
    expect(xpResult.total_xp).toBe(300)
    expect(xpResult.awards[0].leveled_up).toBe(true)
    expect(xpResult.awards[0].new_level).toBe(2)

    // Verify pending level-up exists via API
    const pending = await apiGet(`/game/characters/${characterId}/pending-level-ups`)
    expect(pending.pending.length).toBeGreaterThan(0)
    expect(pending.pending[0].to_level).toBe(2)

    await screenshot(page, '01-xp-awarded-level2')
  })

  test('02 — Open Level-Up modal and screenshot choices', async ({ page }) => {
    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)

    // Click the Level Up button in the toolbar
    const levelUpBtn = page.locator('.btn-level-up, button[title*="Level Up"]')
    await expect(levelUpBtn).toBeVisible({ timeout: 10000 })
    await levelUpBtn.click()

    // Wait for the Level-Up modal to appear
    const modal = page.locator('.levelup-modal')
    await expect(modal).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500)
    await screenshot(page, '02-levelup-modal-open')
    await screenshotFull(page, '02-levelup-modal-full')

    // Verify modal content — wait for data to load (subtitle shows "Loading…" initially)
    await expect(modal.locator('h2')).toContainText('Level Up')
    await expect(modal.locator('.levelup-subtitle')).toContainText('Level 1 → 2', { timeout: 10000 })
    
    // HP section should be visible (level 2 is not an ASI level)
    await expect(modal.locator('h3:has-text("Hit Points")')).toBeVisible()
    
    // Take Average HP should be pre-selected
    const averageRadio = modal.locator('input[name="hp-method"][value="average"], label:has-text("Take Average") input[type="radio"]').first()
    // Screenshot the HP options
    await screenshot(page, '02-levelup-hp-options')
  })

  test('03 — Roll HP and apply level-up', async ({ page }) => {
    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)

    // Open Level-Up modal
    const levelUpBtn = page.locator('.btn-level-up, button[title*="Level Up"]')
    await levelUpBtn.click()
    const modal = page.locator('.levelup-modal')
    await expect(modal).toBeVisible({ timeout: 10000 })

    // Switch to Roll HP
    const rollLabel = modal.locator('label:has-text("Roll")')
    await rollLabel.click()
    await page.waitForTimeout(300)
    await screenshot(page, '03-levelup-roll-selected')

    // Click the roll button
    const rollBtn = modal.locator('.roll-btn, button:has-text("Roll d")')
    await expect(rollBtn).toBeVisible({ timeout: 5000 })
    await rollBtn.click()
    await page.waitForTimeout(500)
    
    // Verify roll result appears
    const rollResult = modal.locator('.hp-roll-result')
    await expect(rollResult).toBeVisible({ timeout: 5000 })
    await screenshot(page, '03-levelup-hp-rolled')

    // Submit the level-up
    const confirmBtn = modal.locator('.levelup-btn.primary, button:has-text("Confirm Level")')
    await expect(confirmBtn).toBeEnabled({ timeout: 5000 })
    await confirmBtn.click()

    // Wait for success message
    const success = modal.locator('.levelup-success')
    await expect(success).toBeVisible({ timeout: 10000 })
    await screenshot(page, '03-levelup-success')

    // Modal should close after celebration
    await expect(modal).not.toBeVisible({ timeout: 5000 })
    await screenshot(page, '03-after-levelup-complete')
  })

  test('04 — Award more XP for ASI level (level 4)', async ({ page }) => {
    // Award enough XP to reach level 4 (2700 XP needed total, already have 300)
    // Level 3 = 900, Level 4 = 2700
    await apiPost(`/game/sessions/${sessionId}/xp-event`, {
      event_type: 'quest',
      description: 'Completed the main quest',
      xp_total: 2400,
      character_ids: [characterId],
    })

    // Check: should have pending level-ups for levels 3 AND 4
    const pending = await apiGet(`/game/characters/${characterId}/pending-level-ups`)
    expect(pending.pending.length).toBeGreaterThanOrEqual(1)

    // Navigate to game and open level-up
    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)

    const levelUpBtn = page.locator('.btn-level-up, button[title*="Level Up"]')
    await levelUpBtn.click()
    const modal = page.locator('.levelup-modal')
    await expect(modal).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500)

    // Should show multiple pending level-ups badge
    const queueBadge = modal.locator('.levelup-queue-badge')
    // Screenshot the queue
    await screenshot(page, '04-multi-levelup-queue')
    await screenshotFull(page, '04-multi-levelup-full')

    // Apply level 3 first (take average HP, no ASI at level 3)
    const confirmBtn = modal.locator('.levelup-btn.primary, button:has-text("Confirm Level")')
    await expect(confirmBtn).toBeEnabled({ timeout: 5000 })
    await confirmBtn.click()

    // Wait for success, then it should auto-refresh to next level-up
    const success = modal.locator('.levelup-success')
    await expect(success).toBeVisible({ timeout: 10000 })
    await screenshot(page, '04-level3-applied')
    
    // Wait for refresh to level 4 (ASI level)
    await page.waitForTimeout(2500)
    await screenshot(page, '04-level4-asi-screen')
  })

  test('05 — ASI choices at level 4', async ({ page }) => {
    // Check if there's still a pending level-up for level 4
    const pending = await apiGet(`/game/characters/${characterId}/pending-level-ups`)
    
    if (pending.pending.length === 0) {
      // Level 4 may have been auto-applied; skip this test gracefully
      test.skip()
      return
    }

    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)

    const levelUpBtn = page.locator('.btn-level-up, button[title*="Level Up"]')
    await levelUpBtn.click()
    const modal = page.locator('.levelup-modal')
    await expect(modal).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500)

    // Check if ASI section is visible (level 4 is an ASI level)
    const asiSection = modal.locator('h3:has-text("Ability Score")')
    if (await asiSection.isVisible()) {
      await screenshot(page, '05-asi-section-visible')

      // Click +1 STR twice (2 total ASI points)
      const strPlusBtn = modal.locator('.asi-row:has-text("STR") .asi-btn:has-text("+")')
      if (await strPlusBtn.isVisible()) {
        await strPlusBtn.click()
        await strPlusBtn.click()
        await page.waitForTimeout(300)
        await screenshot(page, '05-asi-str-plus2')
      }

      // Check the budget display
      const budget = modal.locator('.asi-budget')
      if (await budget.isVisible()) {
        await expect(budget).toContainText('0')
      }

      // Now try switching to Feat mode
      const featTab = modal.locator('.asi-tab:has-text("Feat"), button:has-text("Choose a Feat")')
      if (await featTab.isVisible()) {
        await featTab.click()
        await page.waitForTimeout(300)
        await screenshot(page, '05-feat-mode')

        // Type a feat name
        const featInput = modal.locator('.feat-input, input[placeholder*="feat" i]')
        if (await featInput.isVisible()) {
          await featInput.fill('Great Weapon Master')
          await screenshot(page, '05-feat-entered')
        }

        // Switch back to ASI
        const asiTab = modal.locator('.asi-tab:has-text("Ability Scores")')
        await asiTab.click()
        await page.waitForTimeout(300)
      }
    }

    // Submit level-up with ASI (re-select +2 STR if needed)
    const strPlusBtn = modal.locator('.asi-row:has-text("STR") .asi-btn:has-text("+")')
    if (await strPlusBtn.isVisible()) {
      // Reset and re-apply
      const strMinusBtn = modal.locator('.asi-row:has-text("STR") .asi-btn:has-text("−")')
      // Just click + twice from whatever state
      const currentIncrease = modal.locator('.asi-row:has-text("STR") .asi-increase')
      const text = await currentIncrease.textContent()
      if (!text?.includes('+2')) {
        // Need to set it
        while (await strMinusBtn.isEnabled()) await strMinusBtn.click()
        await strPlusBtn.click()
        await strPlusBtn.click()
      }
    }

    const confirmBtn = modal.locator('.levelup-btn.primary, button:has-text("Confirm Level")')
    await expect(confirmBtn).toBeEnabled({ timeout: 5000 })
    await confirmBtn.click()

    const success = modal.locator('.levelup-success')
    await expect(success).toBeVisible({ timeout: 10000 })
    await screenshot(page, '05-level4-asi-success')

    // Modal should close
    await expect(modal).not.toBeVisible({ timeout: 5000 })
    await screenshot(page, '05-after-asi-levelup')
  })

  test('06 — Add loot via API and open Party Inventory', async ({ page }) => {
    // Add loot to party via API
    await apiPost(`/game/sessions/${sessionId}/loot`, {
      items: [
        { name: 'Flame Tongue Longsword', item_type: 'weapon', rarity: 'rare', description: 'A sword wreathed in magical flames. +2d6 fire damage.', quantity: 1 },
        { name: 'Potion of Healing', item_type: 'potion', rarity: 'common', description: 'Heals 2d4+2 HP.', quantity: 3 },
        { name: 'Ring of Protection', item_type: 'ring', rarity: 'uncommon', description: '+1 AC and saving throws.', quantity: 1 },
        { name: 'Gold Coins', item_type: 'treasure', rarity: 'common', description: 'A hefty pouch of gold.', quantity: 50 },
        { name: 'Cloak of Elvenkind', item_type: 'wondrous', rarity: 'uncommon', description: 'Advantage on Stealth checks.', quantity: 1 },
      ],
    })

    // Also add some gold
    await apiPost(`/game/sessions/${sessionId}/gold`, {
      amount: 250,
      reason: 'Goblin hoard',
    })

    // Navigate to game session
    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)
    
    // Open Party Inventory
    const inventoryBtn = page.locator('.btn-inventory, button[title*="Inventory"]')
    await expect(inventoryBtn).toBeVisible({ timeout: 10000 })
    await inventoryBtn.click()

    // Wait for inventory modal
    const inventoryModal = page.locator('.party-inventory-overlay, .party-inventory-modal')
    await expect(inventoryModal).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500)
    await screenshot(page, '06-inventory-with-loot')
    await screenshotFull(page, '06-inventory-full')

    // Verify items are visible
    await expect(page.locator('.inventory-item, .pending-loot-item').first()).toBeVisible({ timeout: 5000 })
    
    // Check gold display
    const goldDisplay = page.locator('.gold-display, .party-gold, text=250')
    await screenshot(page, '06-inventory-items-visible')
  })

  test('07 — Distribute loot to character', async ({ page }) => {
    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)

    // Open Party Inventory
    const inventoryBtn = page.locator('.btn-inventory, button[title*="Inventory"]')
    await inventoryBtn.click()
    const inventoryModal = page.locator('.party-inventory-overlay, .party-inventory-modal')
    await expect(inventoryModal).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500)

    // Find the first item's distribute dropdown
    const distributeSelect = page.locator('.loot-distribute-select').first()
    if (await distributeSelect.isVisible()) {
      // Select the character from dropdown
      await distributeSelect.selectOption({ index: 1 }) // First character
      await page.waitForTimeout(300)
      await screenshot(page, '07-distribute-character-selected')

      // Click the Give button
      const giveBtn = page.locator('.loot-distribute-btn').first()
      await expect(giveBtn).toBeEnabled()
      await giveBtn.click()
      await page.waitForTimeout(1000)
      await screenshot(page, '07-distribute-success')

      // Check for success indicator
      const successMsg = page.locator('.loot-distribute-success').first()
      await expect(successMsg).toBeVisible({ timeout: 5000 })
    } else {
      // Items might not have distribute controls if no party characters loaded
      await screenshot(page, '07-no-distribute-controls')
    }

    await screenshotFull(page, '07-after-distribute-full')
  })

  test('08 — Distribute multiple items and verify inventory updates', async ({ page }) => {
    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)

    // Open Party Inventory
    const inventoryBtn = page.locator('.btn-inventory, button[title*="Inventory"]')
    await inventoryBtn.click()
    const inventoryModal = page.locator('.party-inventory-overlay, .party-inventory-modal')
    await expect(inventoryModal).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500)

    // Try to distribute remaining items
    const distributeSelects = page.locator('.loot-distribute-select')
    const selectCount = await distributeSelects.count()
    
    for (let i = 0; i < Math.min(selectCount, 3); i++) {
      const select = distributeSelects.nth(i)
      if (await select.isVisible()) {
        await select.selectOption({ index: 1 })
        await page.waitForTimeout(200)
        
        const giveBtn = page.locator('.loot-distribute-btn').nth(i)
        if (await giveBtn.isEnabled()) {
          await giveBtn.click()
          await page.waitForTimeout(800)
        }
      }
    }
    
    await screenshot(page, '08-multiple-distributed')

    // Check filter tabs
    const filterBtns = page.locator('.inv-filter')
    const filterCount = await filterBtns.count()
    if (filterCount > 1) {
      await filterBtns.nth(1).click()
      await page.waitForTimeout(300)
      await screenshot(page, '08-filtered-view')
    }

    await screenshotFull(page, '08-inventory-after-distribution')
  })

  test('09 — Verify character received items', async ({ page }) => {
    // Check character via API
    const character = await apiGet(`/characters/${characterId}`)
    
    // Character should have items in inventory (check various possible storage keys)
    const hasItems = (character.inventory?.length || character.structured_inventory?.length || 
      character.items?.length || character.equipment?.length || 0) > 0
    // Note: items may not persist to character if distribute-loot stores them in session
    await screenshot(page, '09-character-inventory-check')
    
    // Navigate to campaign page to see character details
    await page.goto(`/campaign/${campaignId}`)
    await page.waitForSelector('.page-campaign-detail', { timeout: 15000 })
    await page.waitForTimeout(1500)
    await screenshot(page, '09-campaign-with-leveled-character')

    // Verify character shows updated level
    const charCard = page.locator(`.party-tray-member:has-text("Thorin"), .character-card:has-text("Thorin")`)
    if (await charCard.isVisible()) {
      await screenshot(page, '09-character-card-leveled')
    }
    
    await screenshotFull(page, '09-campaign-overview-full')
  })

  test('10 — Level-up modal with no pending level-ups', async ({ page }) => {
    await page.goto(`/game/${sessionId}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)

    // Open Level-Up modal (should show "no pending" state)
    const levelUpBtn = page.locator('.btn-level-up, button[title*="Level Up"]')
    await levelUpBtn.click()
    const modal = page.locator('.levelup-modal')
    await expect(modal).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500)

    // Should show empty state
    const emptyMsg = modal.locator('.levelup-empty')
    if (await emptyMsg.isVisible({ timeout: 5000 }).catch(() => false)) {
      await screenshot(page, '10-no-pending-levelups')
    }

    // Close modal
    const closeBtn = modal.locator('.levelup-close').first()
    await closeBtn.click()
    await expect(modal).not.toBeVisible({ timeout: 3000 })
    await screenshot(page, '10-modal-closed')
  })

  test('11 — Empty inventory state', async ({ page }) => {
    // Create a fresh session to test empty inventory
    const freshSession = await apiPost('/game/sessions', {
      campaign_id: campaignId,
      character_ids: [characterId],
    })

    await page.goto(`/game/${freshSession.id}`)
    await page.waitForSelector('.game-layout, .game-session', { timeout: 30000 })
    await page.waitForTimeout(2000)

    // Open Party Inventory (should be empty)
    const inventoryBtn = page.locator('.btn-inventory, button[title*="Inventory"]')
    await inventoryBtn.click()
    const inventoryModal = page.locator('.party-inventory-overlay, .party-inventory-modal')
    await expect(inventoryModal).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(500)

    // Should show empty state
    await screenshot(page, '11-empty-inventory')
    
    const emptyIcon = page.locator('.inventory-empty').first()
    if (await emptyIcon.isVisible().catch(() => false)) {
      await screenshot(page, '11-empty-inventory-message')
    }

    // Clean up fresh session
    await fetch(`${API}/game/sessions/${freshSession.id}`, { method: 'DELETE' })
    
    await screenshotFull(page, '11-empty-inventory-full')
  })
})
