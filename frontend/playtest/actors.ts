/** Actors — Host laptop, TV (DM display), and Phone players.
 * Each actor owns one instrumented browser context and interacts with the
 * real UI exactly the way a human at the table would.
 */
import type { Browser, BrowserContext, Page } from 'playwright-core';
import { devices } from 'playwright-core';
import * as path from 'path';
import type { EventBus } from './events';
import type { PlaytestConfig } from './config';
import { instrumentPage, ScreenshotTaker } from './instrument';
import { humanType, humanTap, thinkTime, readTime, sleep, settle } from './human';
import type { PersonaBrain } from './brain';

const IPHONE = devices['iPhone 14'];

async function newActorContext(
  browser: Browser,
  cfg: PlaytestConfig,
  actor: string,
  bus: EventBus,
  opts: { viewport: { width: number; height: number }; mobile?: boolean },
): Promise<{ context: BrowserContext; page: Page }> {
  const context = await browser.newContext({
    baseURL: cfg.baseUrl,
    viewport: opts.viewport,
    ...(opts.mobile
      ? { userAgent: IPHONE.userAgent, hasTouch: true, isMobile: true, deviceScaleFactor: 3 }
      : {}),
    permissions: [],
  });
  await context.tracing.start({ screenshots: false, snapshots: true, title: actor });
  const page = await context.newPage();
  instrumentPage(page, actor, bus);
  bus.emit(actor, 'context', { viewport: opts.viewport, mobile: !!opts.mobile });
  return { context, page };
}

async function stopActor(context: BrowserContext, cfg: PlaytestConfig, actor: string): Promise<void> {
  try {
    await context.tracing.stop({ path: path.join(cfg.runDir, `trace-${actor}.zip`) });
  } catch { /* trace already stopped */ }
  await context.close().catch(() => {});
}

/** The host's laptop: creates the campaign, party, and multiplayer lobby. */
export class HostActor {
  static readonly NAME = 'host';
  context!: BrowserContext;
  page!: Page;
  sessionId = '';
  campaignId = '';
  roomCode = '';

  constructor(private cfg: PlaytestConfig, private bus: EventBus, private shots: ScreenshotTaker) {}

  async start(browser: Browser): Promise<void> {
    ({ context: this.context, page: this.page } = await newActorContext(
      browser, this.cfg, HostActor.NAME, this.bus, { viewport: { width: 1280, height: 800 } },
    ));
  }

  /** Home → featured campaign → 4 premade heroes → Host Multiplayer → lobby. */
  async createGameNight(partySize: number): Promise<void> {
    const { page, bus, shots } = this;
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.featured-card', { timeout: 30_000 });
    await shots.beat(page, HostActor.NAME, 'home', bus);

    await thinkTime();
    await humanTap(page.locator('.featured-card').first());
    await page.waitForURL('**/campaign/**', { timeout: 30_000 });
    this.campaignId = page.url().split('/campaign/')[1];
    bus.emit(HostActor.NAME, 'action', { name: 'campaign-created', campaignId: this.campaignId });
    await settle(page);
    await shots.beat(page, HostActor.NAME, 'campaign-detail', bus);

    for (let i = 0; i < partySize; i++) {
      // First hero: mode chooser; subsequent: "+ Add" in the party tray
      const opener = i === 0
        ? page.locator('[data-testid=btn-premade]')
        : page.locator('.party-tray-add');
      await opener.waitFor({ timeout: 15_000 });
      await humanTap(opener);
      await page.waitForSelector('[data-testid=character-picker]', { timeout: 15_000 });
      await humanTap(page.locator('.picker-card').nth(i));
      await sleep(600);
      await humanTap(page.locator('[data-testid=picker-confirm]'));
      await page.waitForSelector('[data-testid=success-banner]', { timeout: 15_000 });
      bus.emit(HostActor.NAME, 'action', { name: 'hero-added', index: i });
      await sleep(800);
    }
    await shots.beat(page, HostActor.NAME, 'party-assembled', bus);

    await thinkTime();
    await humanTap(page.locator('[data-testid=btn-host-multiplayer]'));
    await page.waitForURL('**/lobby/**', { timeout: 30_000 });
    this.sessionId = page.url().split('/lobby/')[1];
    bus.emit(HostActor.NAME, 'action', { name: 'lobby-opened', sessionId: this.sessionId });

    // Wait for the room code to load (it starts as "...")
    await page.waitForFunction(() => {
      const el = document.querySelector('.lobby-room-code');
      return !!el && el.textContent !== null && el.textContent.trim().length >= 4 && el.textContent.trim() !== '...';
    }, undefined, { timeout: 30_000 });
    this.roomCode = (await page.locator('.lobby-room-code').textContent())?.trim() || '';
    bus.emit(HostActor.NAME, 'action', { name: 'room-code', roomCode: this.roomCode });
    await shots.beat(page, HostActor.NAME, 'lobby', bus);
  }

  /** Read the lobby roster as the host sees it. */
  async lobbyRoster(): Promise<string[]> {
    return this.page.locator('.lobby-player-name').allTextContents();
  }

  /** DM decision: an encounter begins (the one thing a human DM would trigger). */
  async startCombat(enemies: Array<Record<string, unknown>>): Promise<void> {
    const t0 = Date.now();
    const res = await this.page.request.post(
      `${this.cfg.baseUrl}/api/game/sessions/${this.sessionId}/start-combat`,
      { data: { enemies } },
    );
    this.bus.emit(HostActor.NAME, 'action', {
      name: 'start-combat', status: res.status(), ms: Date.now() - t0, enemies: enemies.length,
    });
  }

  async endSession(): Promise<void> {
    const res = await this.page.request.post(
      `${this.cfg.baseUrl}/api/game/sessions/${this.sessionId}/end`,
    ).catch(() => null);
    this.bus.emit(HostActor.NAME, 'action', { name: 'end-session', status: res?.status() ?? 'failed' });
  }

  async stop(): Promise<void> {
    await stopActor(this.context, this.cfg, HostActor.NAME);
  }
}

/** The living-room TV showing the DM display. Passive but observant. */
export class TVActor {
  static readonly NAME = 'tv';
  context!: BrowserContext;
  page!: Page;

  constructor(private cfg: PlaytestConfig, private bus: EventBus, private shots: ScreenshotTaker) {}

  async start(browser: Browser, sessionId: string): Promise<void> {
    ({ context: this.context, page: this.page } = await newActorContext(
      browser, this.cfg, TVActor.NAME, this.bus, { viewport: { width: 1920, height: 1080 } },
    ));
    await this.page.goto(`/dm/${sessionId}`, { waitUntil: 'domcontentloaded' });
    await this.page.waitForSelector('.dm-display', { timeout: 30_000 });
    this.bus.emit(TVActor.NAME, 'action', { name: 'dm-display-open' });
    await this.shots.beat(this.page, TVActor.NAME, 'dm-display-initial', this.bus);
  }

  async narrationText(): Promise<string> {
    return (await this.page.locator('.dm-narration-text').textContent().catch(() => '')) || '';
  }

  async roomCode(): Promise<string> {
    return ((await this.page.locator('.dm-room-value').textContent().catch(() => '')) || '').trim();
  }

  async hasInitiative(): Promise<boolean> {
    return (await this.page.locator('.dm-initiative').count()) > 0;
  }

  async screenshot(name: string): Promise<void> {
    await this.shots.beat(this.page, TVActor.NAME, name, this.bus);
  }

  async stop(): Promise<void> {
    await stopActor(this.context, this.cfg, TVActor.NAME);
  }
}

/** A player's phone. Joins by room code, picks a character, plays the game. */
export class PhoneActor {
  context!: BrowserContext;
  page!: Page;
  readonly name: string;
  sessionId = '';

  constructor(
    public brain: PersonaBrain,
    private cfg: PlaytestConfig,
    private bus: EventBus,
    private shots: ScreenshotTaker,
  ) {
    this.name = `phone-${brain.persona.playerName.toLowerCase()}`;
  }

  async start(browser: Browser): Promise<void> {
    ({ context: this.context, page: this.page } = await newActorContext(
      browser, this.cfg, this.name, this.bus,
      { viewport: { width: 390, height: 844 }, mobile: true },
    ));
  }

  /** /join → type name + room code → pick character → land on /play. */
  async join(roomCode: string): Promise<void> {
    const { page, bus } = this;
    const t0 = Date.now();
    await page.goto('/join', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.join-game-form', { timeout: 30_000 });
    await this.shots.beat(page, this.name, 'join-page', bus);

    await humanType(page.locator('.join-field input').first(), this.brain.persona.playerName);
    await humanType(page.locator('.join-room-code-input'), roomCode);
    await humanTap(page.locator('.join-game-btn'));

    // Either the character picker appears or we go straight to /play
    const picker = page.locator('.character-picker-grid');
    const outcome = await Promise.race([
      picker.waitFor({ timeout: 30_000 }).then(() => 'picker' as const),
      page.waitForURL('**/play/**', { timeout: 30_000 }).then(() => 'play' as const),
    ]).catch(() => 'timeout' as const);

    if (outcome === 'picker') {
      await this.shots.beat(page, this.name, 'character-picker', bus);
      await thinkTime();
      // Pick MY character by name; fall back to the first card
      const mine = page.locator('.character-picker-card', { hasText: this.brain.persona.characterName });
      const card = (await mine.count()) > 0 ? mine.first() : page.locator('.character-picker-card').first();
      await humanTap(card);
      await page.waitForURL('**/play/**', { timeout: 30_000 });
    } else if (outcome === 'timeout') {
      const err = (await page.locator('.join-error').textContent().catch(() => '')) || 'join timeout';
      bus.emit(this.name, 'error', { where: 'join', error: err });
      throw new Error(`${this.name} failed to join: ${err}`);
    }

    this.sessionId = page.url().split('/play/')[1];
    await page.waitForSelector('.pv-action-input', { timeout: 30_000 });
    bus.emit(this.name, 'probe', { name: 'join-to-play', ms: Date.now() - t0 });
    await this.shots.beat(page, this.name, 'player-view', bus);
  }

  /** Read the latest narration entry in the phone's feed. */
  async latestNarration(): Promise<string> {
    const entries = await this.page.locator('.pv-narrative-entry .pv-entry-text').allTextContents().catch(() => []);
    return entries.length ? entries[entries.length - 1] : '';
  }

  /** Human loop: read the scene, think, type an action, send it. */
  async takeExplorationTurn(scene: string): Promise<string> {
    const { page, bus } = this;
    await readTime(scene);
    const action = await this.brain.decideAction(scene);
    await thinkTime();
    const t0 = Date.now();
    bus.emit(this.name, 'action', { name: 'exploration-action', text: action });
    await humanType(page.locator('.pv-action-input'), action);
    await humanTap(page.locator('.pv-action-btn'));
    // waitingForDM shows "DM is composing…" — wait for it to clear (narration done)
    await page.waitForSelector('.pv-entry-system', { timeout: 10_000 }).catch(() => {});
    await page
      .waitForFunction(() => !document.querySelector('.pv-entry-system'), undefined, { timeout: 120_000 })
      .catch(() => bus.emit(this.name, 'error', { where: 'exploration-turn', error: 'DM response >120s' }));
    bus.emit(this.name, 'probe', { name: 'action-to-narration', ms: Date.now() - t0 });
    return action;
  }

  async isMyTurn(): Promise<boolean> {
    return (await this.page.locator('.pv-turn-badge').count().catch(() => 0)) > 0;
  }

  async hpFraction(): Promise<number> {
    try {
      const txt = (await this.page.locator('.pv-hp .pv-stat-val').textContent()) || '';
      const [hp, max] = txt.split('/').map((s) => parseInt(s.trim(), 10));
      if (Number.isFinite(hp) && Number.isFinite(max) && max > 0) return hp / max;
    } catch { /* sheet hidden */ }
    return 1;
  }

  /** Tap a combat quick action (Attack / Dodge / Use Potion). */
  async takeCombatTurn(): Promise<string> {
    const { page, bus } = this;
    const choice = this.brain.decideCombatAction(await this.hpFraction());
    await thinkTime();
    const t0 = Date.now();
    bus.emit(this.name, 'action', { name: 'combat-action', choice });
    const btn = page.locator('.pv-quick-action-btn', { hasText: choice });
    if ((await btn.count()) === 0 || !(await btn.first().isEnabled())) {
      bus.emit(this.name, 'error', { where: 'combat-turn', error: `quick action "${choice}" not available` });
      return choice;
    }
    await humanTap(btn.first());
    bus.emit(this.name, 'probe', { name: 'combat-action-tapped', ms: Date.now() - t0, choice });
    await sleep(1_500);
    return choice;
  }

  async inCombat(): Promise<boolean> {
    return (await this.page.locator('.pv-initiative-strip').count().catch(() => 0)) > 0;
  }

  async screenshot(name: string): Promise<void> {
    await this.shots.beat(this.page, this.name, name, this.bus);
  }

  async stop(): Promise<void> {
    await stopActor(this.context, this.cfg, this.name);
  }
}
