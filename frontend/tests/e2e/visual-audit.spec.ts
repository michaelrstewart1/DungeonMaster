import { test, expect } from '@playwright/test'

// Visual audit test — screenshots every UI state for review
test.describe('Visual UI Audit', () => {
  test('Home page — empty state', async ({ page }) => {
    await page.route('**/api/campaigns', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
    )
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.hero')).toBeVisible()
    await page.screenshot({ path: 'test-results/audit-01-home-empty.png', fullPage: true })
  })

  test('Home page — with campaigns', async ({ page }) => {
    await page.route('**/api/campaigns', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: '1', name: 'The Lost Mines of Phandelver', description: 'A classic introductory adventure through the Sword Coast', character_ids: ['a', 'b', 'c'], session_ids: [] },
          { id: '2', name: 'Curse of Strahd', description: 'Gothic horror in the demiplane of Barovia', character_ids: ['x'], session_ids: ['s1'] },
          { id: '3', name: 'Tomb of Annihilation', description: 'A death curse plagues the land of Chult', character_ids: [], session_ids: [] },
        ]),
      })
    )
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: 'test-results/audit-02-home-campaigns.png', fullPage: true })
  })

  test('Home page — new campaign form', async ({ page }) => {
    await page.route('**/api/campaigns', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
    )
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.click('.btn-primary')
    await page.waitForSelector('.campaign-form')
    await page.screenshot({ path: 'test-results/audit-03-home-form.png', fullPage: true })
  })

  test('Campaign Detail — mode chooser', async ({ page }) => {
    await page.route('**/api/campaigns/test-1', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'test-1', name: 'The Dragon of Icespire Peak', description: 'A dangerous dragon terrorizes the town of Phandalin', character_ids: [], session_ids: [] }),
      })
    )
    await page.route('**/api/characters?campaign_id=test-1', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
    )
    await page.goto('/campaign/test-1')
    await page.waitForSelector('text=The Dragon of Icespire Peak', { timeout: 5000 })
    await page.screenshot({ path: 'test-results/audit-04-campaign-detail.png', fullPage: true })
  })

  test('Campaign Detail — character picker', async ({ page }) => {
    await page.route('**/api/campaigns/test-1', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'test-1', name: 'The Dragon of Icespire Peak', description: 'A dangerous dragon terrorizes Phandalin', character_ids: [], session_ids: [] }),
      })
    )
    await page.route('**/api/characters?campaign_id=test-1', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
    )
    await page.goto('/campaign/test-1')
    await page.waitForLoadState('networkidle')
    await page.click('[data-testid="btn-premade"]')
    await page.waitForSelector('[data-testid="character-picker"]')
    await page.screenshot({ path: 'test-results/audit-05-picker-gallery.png', fullPage: true })
    
    // Click a character to see detail
    await page.click('[data-testid="picker-card-premade-thorne"]')
    await page.waitForSelector('[data-testid="picker-detail"]')
    await page.screenshot({ path: 'test-results/audit-06-picker-detail.png', fullPage: true })
  })

  test('Campaign Detail — character creator wizard', async ({ page }) => {
    await page.route('**/api/campaigns/test-1', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'test-1', name: 'Epic Quest', description: 'An epic adventure', character_ids: [], session_ids: [] }),
      })
    )
    await page.route('**/api/characters?campaign_id=test-1', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
    )
    await page.goto('/campaign/test-1')
    await page.waitForLoadState('networkidle')
    await page.click('[data-testid="btn-manual"]')
    
    // Step 1: Race
    await page.waitForSelector('[data-testid="step-race"]')
    await page.screenshot({ path: 'test-results/audit-07-creator-race.png', fullPage: true })
    
    // Select elf and go to step 2
    await page.click('[data-testid="race-elf"]')
    await page.click('button:has-text("Next: Choose Class")')
    
    // Step 2: Class
    await page.waitForSelector('[data-testid="step-class"]')
    await page.screenshot({ path: 'test-results/audit-08-creator-class.png', fullPage: true })
    
    // Select wizard and go to step 3
    await page.click('[data-testid="class-wizard"]')
    await page.click('button:has-text("Next: Abilities")')
    
    // Step 3: Abilities
    await page.waitForSelector('[data-testid="step-abilities"]')
    await page.screenshot({ path: 'test-results/audit-09-creator-abilities.png', fullPage: true })
    
    // Go to step 4
    await page.click('button:has-text("Next: Review")')
    
    // Step 4: Review
    await page.waitForSelector('[data-testid="step-review"]')
    await page.screenshot({ path: 'test-results/audit-10-creator-review.png', fullPage: true })
  })

  test('Campaign Detail — character import', async ({ page }) => {
    await page.route('**/api/campaigns/test-1', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'test-1', name: 'Import Test', description: 'Testing import', character_ids: [], session_ids: [] }),
      })
    )
    await page.route('**/api/characters?campaign_id=test-1', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
    )
    await page.goto('/campaign/test-1')
    await page.waitForLoadState('networkidle')
    await page.click('[data-testid="btn-import"]')
    await page.waitForSelector('.character-import')
    await page.screenshot({ path: 'test-results/audit-11-import.png', fullPage: true })
  })

  test('Campaign Detail — with existing characters', async ({ page }) => {
    await page.route('**/api/campaigns/test-1', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'test-1', name: 'Active Campaign', description: 'A campaign with characters', character_ids: ['c1', 'c2'], session_ids: [] }),
      })
    )
    await page.route('**/api/characters?campaign_id=test-1', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'c1', name: 'Thorne Ironfist', race: 'dwarf', class_name: 'fighter', level: 3, hp: 28, max_hp: 34, ac: 18, proficiency_bonus: 2, strength: 16, dexterity: 12, constitution: 15, intelligence: 8, wisdom: 13, charisma: 10, conditions: [], inventory: ['Longsword', 'Chain Mail', 'Shield', 'Handaxes (2)'], spell_slots: {} },
          { id: 'c2', name: 'Lyra Moonwhisper', race: 'elf', class_name: 'wizard', level: 3, hp: 14, max_hp: 18, ac: 12, proficiency_bonus: 2, strength: 8, dexterity: 14, constitution: 12, intelligence: 17, wisdom: 13, charisma: 11, conditions: ['invisible'], inventory: ['Quarterstaff', 'Spellbook', 'Component Pouch', 'Robes of Arcana'], spell_slots: {} },
        ]),
      })
    )
    await page.goto('/campaign/test-1')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: 'test-results/audit-12-with-characters.png', fullPage: true })
  })

  test('Game Session page', async ({ page }) => {
    await page.route('**/api/game/sessions/session-1/state', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'session-1',
          campaign_id: 'test-1',
          phase: 'exploration',
          current_scene: 'You stand at the entrance of a dark cavern. The air is thick with the smell of damp stone and something... else. Torchlight flickers against ancient runes carved into the walls.',
          characters: [],
          combat_state: null,
          game_log: [],
        }),
      })
    )
    // Mock websocket to prevent connection errors
    await page.addInitScript(() => {
      (window as any).WebSocket = class MockWebSocket {
        onopen: any; onclose: any; onmessage: any; onerror: any;
        readyState = 0;
        constructor() { setTimeout(() => { this.readyState = 1; if (this.onopen) this.onopen({}); }, 100); }
        send() {}
        close() { this.readyState = 3; if (this.onclose) this.onclose({}); }
      }
    })
    await page.goto('/game/session-1')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)
    await page.screenshot({ path: 'test-results/audit-13-game-session.png', fullPage: true })
  })
})
