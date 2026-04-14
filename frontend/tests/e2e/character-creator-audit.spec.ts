import { test, expect } from '@playwright/test'

// Visual audit of the comprehensive 5e Character Creator
// Takes screenshots of every step for UI/UX review

test.describe('Character Creator Visual Audit', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('.campaign-card')
    // Click first campaign
    await page.locator('.campaign-card').first().click()
    await page.waitForTimeout(500)
    // Click "Create Custom" to open the character creator
    await page.locator('[data-testid="btn-manual"]').click()
    await page.waitForSelector('.character-creator')
  })

  test('Step 0 - Race selection default', async ({ page }) => {
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step0-race.png', fullPage: true })
  })

  test('Step 0 - Dwarf subraces', async ({ page }) => {
    await page.click('[data-testid="race-dwarf"]')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step0-dwarf-subraces.png', fullPage: true })
  })

  test('Step 0 - Elf subraces', async ({ page }) => {
    await page.click('[data-testid="race-elf"]')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step0-elf-subraces.png', fullPage: true })
  })

  test('Step 1 - Class selection', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step1-class.png', fullPage: true })
  })

  test('Step 1 - Wizard subclass', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.click('[data-testid="class-wizard"]')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step1-wizard-subclass.png', fullPage: true })
  })

  test('Step 2 - Background', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.click('button:has-text("Next: Background")')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step2-background.png', fullPage: true })
  })

  test('Step 3 - Abilities point buy', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.click('button:has-text("Next: Background")')
    await page.click('button:has-text("Next: Abilities")')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step3-pointbuy.png', fullPage: true })
  })

  test('Step 3 - Abilities standard array', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.click('button:has-text("Next: Background")')
    await page.click('button:has-text("Next: Abilities")')
    await page.click('[data-testid="method-standard-array"]')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step3-stdarray.png', fullPage: true })
  })

  test('Step 3 - Abilities roll 4d6', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.click('button:has-text("Next: Background")')
    await page.click('button:has-text("Next: Abilities")')
    await page.click('[data-testid="method-roll"]')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step3-roll.png', fullPage: true })
  })

  test('Step 4 - Skills', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.click('button:has-text("Next: Background")')
    await page.click('button:has-text("Next: Abilities")')
    await page.click('button:has-text("Next: Skills")')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step4-skills.png', fullPage: true })
  })

  test('Step 5 - Equipment', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.click('button:has-text("Next: Background")')
    await page.click('button:has-text("Next: Abilities")')
    await page.click('button:has-text("Next: Skills")')
    await page.click('button:has-text("Next: Equipment")')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step5-equipment.png', fullPage: true })
  })

  test('Step 6 - Details', async ({ page }) => {
    await page.click('button:has-text("Next: Choose Class")')
    await page.click('button:has-text("Next: Background")')
    await page.click('button:has-text("Next: Abilities")')
    await page.click('button:has-text("Next: Skills")')
    await page.click('button:has-text("Next: Equipment")')
    await page.click('button:has-text("Next: Details")')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step6-details.png', fullPage: true })
  })

  test('Step 7 - Review', async ({ page }) => {
    // Select dwarf + hill dwarf for a full build
    await page.click('[data-testid="race-dwarf"]')
    await page.click('[data-testid="subrace-hill-dwarf"]')
    await page.click('button:has-text("Next: Choose Class")')
    // Select cleric + life domain
    await page.click('[data-testid="class-cleric"]')
    await page.click('[data-testid="subclass-life-domain"]')
    await page.click('button:has-text("Next: Background")')
    // Select acolyte
    await page.click('[data-testid="bg-acolyte"]')
    await page.click('button:has-text("Next: Abilities")')
    await page.click('button:has-text("Next: Skills")')
    await page.click('button:has-text("Next: Equipment")')
    // Cleric is a caster - button says "Next: Spells"
    await page.click('button:has-text("Next: Spells")')
    await page.click('button:has-text("Next: Details")')
    await page.fill('#char-name', 'Bromm Stoneforge')
    await page.click('button:has-text("Next: Review")')
    await page.waitForTimeout(200)
    await page.screenshot({ path: 'tests/e2e/screenshots/creator-step7-review.png', fullPage: true })
  })
})
