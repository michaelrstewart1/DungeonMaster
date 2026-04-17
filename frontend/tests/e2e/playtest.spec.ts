/**
 * Interactive playtest script — launches the real game and takes screenshots
 * at each step to evaluate UX from a tabletop player's perspective.
 * 
 * Usage: npx playwright test tests/playtest.ts --headed --timeout=300000
 */
import { test, expect, Page } from '@playwright/test'

const BASE_URL = 'http://192.168.1.94'

async function screenshot(page: Page, name: string) {
  await page.waitForTimeout(1000) // let animations settle
  await page.screenshot({ path: `./playtest-screenshots/${name}.png`, fullPage: false })
  console.log(`📸 Screenshot: ${name}`)
}

test('Full playtest — tabletop user experience', async ({ page }) => {
  test.setTimeout(300_000) // 5 minutes
  await page.setViewportSize({ width: 1920, height: 1080 }) // TV/monitor size

  // ═══════════════════════════════════════════════════════
  // STEP 1: Landing page — what does a new user see?
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 1: Landing page')
  await page.goto(BASE_URL, { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await screenshot(page, '01-landing-page')

  // ═══════════════════════════════════════════════════════
  // STEP 2: Check if there are existing campaigns
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 2: Looking for campaigns or create button')
  // Look for any campaign cards or "create" buttons
  const campaignCards = await page.locator('[class*="campaign"]').count()
  const createButtons = await page.locator('button, a').filter({ hasText: /create|new|start/i }).count()
  console.log(`  Found ${campaignCards} campaign elements, ${createButtons} create/new buttons`)
  await screenshot(page, '02-campaigns-overview')

  // ═══════════════════════════════════════════════════════
  // STEP 3: Try to find and click into an existing campaign/game
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 3: Looking for existing game sessions to join')
  
  // Look for any clickable campaign or "play" / "continue" / "join" links
  const playLinks = await page.locator('a, button').filter({ hasText: /play|continue|join|enter|resume|start/i })
  const playCount = await playLinks.count()
  console.log(`  Found ${playCount} play/continue/join buttons`)
  
  // Also check for campaign name links
  const campaignLinks = await page.locator('a[href*="game"], a[href*="campaign"], a[href*="session"]')
  const linkCount = await campaignLinks.count()
  console.log(`  Found ${linkCount} game/campaign/session links`)
  
  // List all visible links for debugging
  const allLinks = await page.locator('a').all()
  for (const link of allLinks.slice(0, 10)) {
    const href = await link.getAttribute('href')
    const text = await link.textContent()
    console.log(`  Link: "${text?.trim()}" -> ${href}`)
  }

  // List all visible buttons
  const allButtons = await page.locator('button').all()
  for (const btn of allButtons.slice(0, 10)) {
    const text = await btn.textContent()
    console.log(`  Button: "${text?.trim()}"`)
  }

  await screenshot(page, '03-navigation-options')

  // ═══════════════════════════════════════════════════════
  // STEP 4: Navigate to a game session (use existing one from user's screenshot URL)
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 4: Attempting to load the active game session')
  
  // Try the session ID from the user's screenshot
  const knownSessionUrl = `${BASE_URL}/game/fcfa5f72-2db5-4c55-9755-d2635798412d`
  await page.goto(knownSessionUrl, { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000) // wait for WS connections and data load
  await screenshot(page, '04-game-session-initial')

  // ═══════════════════════════════════════════════════════
  // STEP 5: Examine the game session layout
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 5: Examining game layout')
  
  // Check what's visible
  const leftSidebar = page.locator('.game-sidebar-left')
  const mainContent = page.locator('.game-main-content')
  const rightSidebar = page.locator('.game-sidebar-right')
  const chatArea = page.locator('.chat-area')
  const mapArea = page.locator('.map-area')
  const miniMap = page.locator('.mini-map')
  
  console.log(`  Left sidebar visible: ${await leftSidebar.isVisible().catch(() => false)}`)
  console.log(`  Main content visible: ${await mainContent.isVisible().catch(() => false)}`)
  console.log(`  Right sidebar visible: ${await rightSidebar.isVisible().catch(() => false)}`)
  console.log(`  Chat area visible: ${await chatArea.isVisible().catch(() => false)}`)
  console.log(`  Map area visible: ${await mapArea.isVisible().catch(() => false)}`)
  console.log(`  Mini-map visible: ${await miniMap.isVisible().catch(() => false)}`)

  // Measure actual sizes
  const mainBox = await mainContent.boundingBox().catch(() => null)
  const chatBox = await chatArea.boundingBox().catch(() => null)
  const leftBox = await leftSidebar.boundingBox().catch(() => null)
  const rightBox = await rightSidebar.boundingBox().catch(() => null)
  
  if (mainBox) console.log(`  Main content: ${Math.round(mainBox.width)}x${Math.round(mainBox.height)} at (${Math.round(mainBox.x)},${Math.round(mainBox.y)})`)
  if (chatBox) console.log(`  Chat area: ${Math.round(chatBox.width)}x${Math.round(chatBox.height)} at (${Math.round(chatBox.x)},${Math.round(chatBox.y)})`)
  if (leftBox) console.log(`  Left sidebar: ${Math.round(leftBox.width)}x${Math.round(leftBox.height)}`)
  if (rightBox) console.log(`  Right sidebar: ${Math.round(rightBox.width)}x${Math.round(rightBox.height)}`)

  await screenshot(page, '05-layout-analysis')

  // ═══════════════════════════════════════════════════════
  // STEP 6: Read the chat messages  
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 6: Reading chat history')
  const messages = await page.locator('.chat-message, .dm-message, [class*="message"]').all()
  console.log(`  Total message elements: ${messages.length}`)
  for (const msg of messages.slice(-5)) {
    const text = await msg.textContent()
    const cls = await msg.getAttribute('class')
    console.log(`  [${cls?.slice(0, 30)}] ${text?.trim().slice(0, 100)}...`)
  }

  // ═══════════════════════════════════════════════════════
  // STEP 7: Check the input area — can we type and send?
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 7: Testing input area')
  const inputField = page.locator('input[type="text"], textarea, [contenteditable]').first()
  const sendButton = page.locator('button').filter({ hasText: /send/i }).first()
  
  console.log(`  Input field visible: ${await inputField.isVisible().catch(() => false)}`)
  console.log(`  Send button visible: ${await sendButton.isVisible().catch(() => false)}`)
  
  // Check placeholder text
  const placeholder = await inputField.getAttribute('placeholder').catch(() => null)
  console.log(`  Placeholder: "${placeholder}"`)

  await screenshot(page, '06-input-area')

  // ═══════════════════════════════════════════════════════
  // STEP 8: Check action buttons (Look Around, Talk to NPC, etc.)
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 8: Checking quick action buttons')
  const quickActions = await page.locator('button').all()
  for (const btn of quickActions) {
    const text = (await btn.textContent())?.trim()
    const visible = await btn.isVisible()
    if (visible && text && text.length < 50) {
      console.log(`  Action button: "${text}"`)
    }
  }
  
  await screenshot(page, '07-action-buttons')

  // ═══════════════════════════════════════════════════════
  // STEP 9: Check left sidebar components in detail
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 9: Left sidebar detail')
  
  // Party members
  const partyMembers = await page.locator('[class*="party"], [class*="character"]').all()
  console.log(`  Party member elements: ${partyMembers.length}`)

  // Environment panel
  const envPanel = page.locator('[class*="environment"], [class*="atmosphere"]')
  console.log(`  Environment panel visible: ${await envPanel.first().isVisible().catch(() => false)}`)

  // Screenshot just the left sidebar area
  if (leftBox) {
    await page.screenshot({ 
      path: './playtest-screenshots/08-left-sidebar-detail.png',
      clip: { x: 0, y: 0, width: leftBox.width + 20, height: leftBox.height }
    })
    console.log('📸 Screenshot: 08-left-sidebar-detail')
  }

  // ═══════════════════════════════════════════════════════
  // STEP 10: Try sending a player action
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 10: Sending a test action')
  
  if (await inputField.isVisible().catch(() => false)) {
    await inputField.fill('I look around the room carefully, checking for any hidden passages or traps.')
    await screenshot(page, '09-typed-action')
    
    // Click send
    if (await sendButton.isVisible().catch(() => false)) {
      await sendButton.click()
      console.log('  ✅ Sent action via Send button')
    } else {
      await inputField.press('Enter')
      console.log('  ✅ Sent action via Enter key')
    }
    
    // Wait for DM response
    console.log('  ⏳ Waiting for DM response...')
    await page.waitForTimeout(15000) // Gemini should respond in ~5-10s
    await screenshot(page, '10-dm-response')
    
    // Read the DM's response
    const latestMessages = await page.locator('.dm-message, [class*="dm-msg"], [class*="narration"]').all()
    if (latestMessages.length > 0) {
      const lastMsg = latestMessages[latestMessages.length - 1]
      const text = await lastMsg.textContent()
      console.log(`  DM responded: "${text?.trim().slice(0, 200)}..."`)
    }
  }

  // ═══════════════════════════════════════════════════════  
  // STEP 11: Check right sidebar (combat panel, etc.)
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 11: Right sidebar')
  const rightPanelContent = await rightSidebar.textContent().catch(() => '')
  console.log(`  Right panel content: "${rightPanelContent?.trim().slice(0, 200)}"`)
  
  if (rightBox) {
    await page.screenshot({
      path: './playtest-screenshots/11-right-sidebar.png', 
      clip: { x: rightBox.x - 5, y: 0, width: rightBox.width + 10, height: rightBox.height }
    })
    console.log('📸 Screenshot: 11-right-sidebar')
  }

  // ═══════════════════════════════════════════════════════
  // STEP 12: Check bottom bar (atmosphere, time, etc.)
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 12: Bottom/status bar')
  const statusElements = await page.locator('[class*="status"], [class*="time"], [class*="weather"], [class*="atmosphere"]').all()
  for (const el of statusElements) {
    const text = (await el.textContent())?.trim()
    if (text && text.length < 100) {
      console.log(`  Status element: "${text}"`)
    }
  }
  
  // ═══════════════════════════════════════════════════════
  // STEP 13: Try "Look Around" quick action
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 13: Testing Look Around quick action')
  const lookAroundBtn = page.locator('button').filter({ hasText: /look around/i }).first()
  if (await lookAroundBtn.isVisible().catch(() => false)) {
    await lookAroundBtn.click()
    console.log('  ✅ Clicked Look Around')
    await page.waitForTimeout(10000)
    await screenshot(page, '12-look-around-response')
  } else {
    console.log('  ❌ Look Around button not found/visible')
  }

  // ═══════════════════════════════════════════════════════
  // STEP 14: Full page final screenshot  
  // ═══════════════════════════════════════════════════════
  console.log('\n🎮 STEP 14: Final state')
  await screenshot(page, '13-final-state')

  // ═══════════════════════════════════════════════════════
  // UX ANALYSIS SUMMARY
  // ═══════════════════════════════════════════════════════
  console.log('\n' + '═'.repeat(60))
  console.log('📋 UX ANALYSIS NOTES')
  console.log('═'.repeat(60))
  console.log('Layout dimensions at 1920x1080:')
  if (leftBox) console.log(`  Left sidebar: ${Math.round(leftBox.width)}px (${Math.round(leftBox.width/1920*100)}% of screen)`)
  if (mainBox) console.log(`  Main content: ${Math.round(mainBox.width)}px (${Math.round(mainBox.width/1920*100)}% of screen)`)
  if (rightBox) console.log(`  Right sidebar: ${Math.round(rightBox.width)}px (${Math.round(rightBox.width/1920*100)}% of screen)`)
  if (chatBox) console.log(`  Chat area height: ${Math.round(chatBox.height)}px (${Math.round(chatBox.height/1080*100)}% of screen)`)
  console.log('═'.repeat(60))
})
