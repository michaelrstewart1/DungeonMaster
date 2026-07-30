/** Human-like input pacing: keystroke cadence, think time, read time. */
import type { Page, Locator } from 'playwright-core';

function jitter(base: number, spread: number): number {
  return Math.max(0, base + (Math.random() * 2 - 1) * spread);
}

export async function sleep(ms: number): Promise<void> {
  await new Promise((r) => setTimeout(r, ms));
}

/** Type like a human: 60-90ms per key with occasional pauses. */
export async function humanType(locator: Locator, text: string): Promise<void> {
  await locator.click();
  for (const ch of text) {
    await locator.pressSequentially(ch, { delay: 0 });
    await sleep(jitter(75, 30));
    if (Math.random() < 0.06) await sleep(jitter(350, 150)); // glance at the TV
  }
}

/** Pause proportional to how much text a human would need to read. */
export async function readTime(text: string, wpm = 300): Promise<void> {
  const words = text.split(/\s+/).length;
  const ms = Math.min(12_000, Math.max(800, (words / wpm) * 60_000));
  await sleep(jitter(ms, ms * 0.2));
}

/** "Hmm, what do I do…" — decision pause before acting. */
export async function thinkTime(): Promise<void> {
  await sleep(jitter(2_200, 1_500));
}

/** Tap like a finger — small pre-tap delay. */
export async function humanTap(locator: Locator): Promise<void> {
  await sleep(jitter(300, 150));
  await locator.click();
}

export async function settle(page: Page, ms = 500): Promise<void> {
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  await sleep(ms);
}
