import { test, expect } from '@playwright/test'

const BASE = process.env.TEST_URL || 'http://192.168.1.94'

test.describe('Background art visibility', () => {
  test('landscape slideshow is visible on home page', async ({ page }) => {
    // Navigate to the home page
    await page.goto(BASE, { waitUntil: 'networkidle' })
    await page.waitForTimeout(3000) // Wait for fade-in (200ms delay + transition)

    // Check that the slideshow container exists
    const slideshow = page.locator('.home-bg-slideshow')
    await expect(slideshow).toBeVisible()

    // Check that at least one scene div has opacity > 0
    const scenes = page.locator('.home-bg-scene')
    const count = await scenes.count()
    console.log(`Found ${count} scene divs`)

    let anyVisible = false
    for (let i = 0; i < count; i++) {
      const opacity = await scenes.nth(i).evaluate(el => {
        const style = window.getComputedStyle(el)
        return {
          opacity: style.opacity,
          bgImage: style.backgroundImage,
          display: style.display,
          visibility: style.visibility,
          width: el.clientWidth,
          height: el.clientHeight,
        }
      })
      console.log(`Scene ${i}:`, JSON.stringify(opacity))
      if (parseFloat(opacity.opacity) > 0 && opacity.bgImage !== 'none') {
        anyVisible = true
      }
    }

    // Check hero section opacity
    const heroOpacity = await page.locator('.hero').evaluate(el => {
      const style = window.getComputedStyle(el)
      return { background: style.background, opacity: style.opacity }
    })
    console.log('Hero:', JSON.stringify(heroOpacity))

    // Check if page-home has overflow hidden or transform that could clip
    const pageHome = await page.locator('.page-home').evaluate(el => {
      const style = window.getComputedStyle(el)
      return {
        overflow: style.overflow,
        transform: style.transform,
        position: style.position,
        width: el.clientWidth,
        height: el.clientHeight,
      }
    })
    console.log('page-home:', JSON.stringify(pageHome))

    // Take screenshot of just the top of the page
    await page.screenshot({ path: './test-results/bg-visibility-full.png', fullPage: false })

    // Take screenshot after 15s to see if crossfade works
    await page.waitForTimeout(12000)
    await page.screenshot({ path: './test-results/bg-visibility-after-fade.png', fullPage: false })

    // Recheck scene opacities after waiting
    for (let i = 0; i < count; i++) {
      const opacity = await scenes.nth(i).evaluate(el => {
        return { opacity: window.getComputedStyle(el).opacity, bgImage: window.getComputedStyle(el).backgroundImage }
      })
      console.log(`Scene ${i} after wait:`, JSON.stringify(opacity))
    }

    expect(anyVisible).toBe(true)
  })

  test('campaign thumbnails load correctly', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle' })
    await page.waitForSelector('.featured-card', { timeout: 10000 })

    const cards = page.locator('.featured-card')
    const cardCount = await cards.count()
    console.log(`Found ${cardCount} featured campaign cards`)

    for (let i = 0; i < cardCount; i++) {
      const artDiv = cards.nth(i).locator('.featured-card-art')
      const bgImage = await artDiv.evaluate(el => window.getComputedStyle(el).backgroundImage)
      console.log(`Campaign card ${i} bg: ${bgImage}`)
    }

    await page.screenshot({ path: './test-results/campaign-cards.png', fullPage: false })
    expect(cardCount).toBeGreaterThan(0)
  })
})
