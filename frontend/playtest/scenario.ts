/** The "family game night" scenario — the full arc a real table goes through:
 * host sets up → phones join → exploration → an encounter → resolution.
 * Every beat is instrumented; chaos is injected mid-flight when enabled.
 */
import type { Browser } from 'playwright-core';
import type { PlaytestConfig } from './config';
import type { EventBus } from './events';
import { ScreenshotTaker } from './instrument';
import { HostActor, TVActor, PhoneActor } from './actors';
import { PersonaBrain, PERSONAS } from './brain';
import type { Persona } from './brain';
import { phoneOffline, phoneRefresh, throttlePhone, tvRefresh } from './chaos';
import { sleep } from './human';

const ENCOUNTER = [
  { name: 'Goblin Skirmisher', hp: 7, ac: 13, cr: 0.25, count: 2 },
  { name: 'Goblin Boss', hp: 21, ac: 15, cr: 1, count: 1 },
];

export async function runGameNight(browser: Browser, cfg: PlaytestConfig, bus: EventBus): Promise<void> {
  const shots = new ScreenshotTaker(cfg.runDir);
  const host = new HostActor(cfg, bus, shots);
  const tv = new TVActor(cfg, bus, shots);
  const phones: PhoneActor[] = PERSONAS.slice(0, cfg.players).map(
    (p: Persona) => new PhoneActor(
      new PersonaBrain(p, cfg.ollamaUrl, cfg.ollamaModel, cfg.llmBrains, bus, `phone-${p.playerName.toLowerCase()}`),
      cfg, bus, shots,
    ),
  );

  try {
    // ── Act 1: setup ────────────────────────────────────────────────
    bus.emit('runner', 'phase', { name: 'setup' });
    await host.start(browser);
    await host.createGameNight(cfg.players);
    await tv.start(browser, host.sessionId);

    const tvCode = await tv.roomCode();
    if (tvCode && tvCode !== host.roomCode) {
      bus.emit('runner', 'issue', { name: 'room-code-mismatch', lobby: host.roomCode, tv: tvCode });
    }

    // ── Act 2: players join (staggered, like people pulling out phones) ──
    bus.emit('runner', 'phase', { name: 'join' });
    for (const phone of phones) {
      await phone.start(browser);
      const tJoin = Date.now();
      await phone.join(host.roomCode);
      // Latency probe: how long until the host's lobby shows the new player?
      const roster = await pollUntil(
        async () => (await host.lobbyRoster()).some((n: string) => n.includes(phone.brain.persona.playerName)),
        20_000,
      );
      bus.emit('runner', 'probe', {
        name: 'join-to-lobby-roster', player: phone.brain.persona.playerName,
        ms: Date.now() - tJoin, visible: roster,
      });
      if (!roster) bus.emit('runner', 'issue', { name: 'lobby-roster-missing-player', player: phone.brain.persona.playerName });
      await sleep(1_000 + Math.random() * 2_000);
    }
    await shots.beat(host.page, 'host', 'lobby-full', bus);
    await tv.screenshot('all-joined');

    // ── Act 3: exploration rounds ───────────────────────────────────
    bus.emit('runner', 'phase', { name: 'exploration' });
    for (let round = 0; round < cfg.explorationRounds; round++) {
      for (const phone of phones) {
        const scene = await phone.latestNarration() || 'The adventure begins in a torch-lit dungeon entrance.';
        const tvBefore = await tv.narrationText();
        const t0 = Date.now();
        const action = await phone.takeExplorationTurn(scene);
        // Probe: does the TV narration react to this player's action?
        const tvUpdated = await pollUntil(async () => (await tv.narrationText()) !== tvBefore, 90_000);
        bus.emit('runner', 'probe', {
          name: 'action-to-tv-narration', player: phone.brain.persona.playerName,
          ms: Date.now() - t0, updated: tvUpdated, action,
        });
        if (!tvUpdated) {
          bus.emit('runner', 'issue', {
            name: 'tv-narration-stale', player: phone.brain.persona.playerName, action,
          });
        }
      }
      await tv.screenshot(`exploration-round-${round + 1}`);
    }

    // ── Chaos: wifi blip + refresh during downtime ──────────────────
    if (cfg.chaos && phones.length >= 2) {
      bus.emit('runner', 'phase', { name: 'chaos-exploration' });
      await phoneRefresh(phones[1], bus);
      await throttlePhone(phones[phones.length - 1], bus, true);
      await tvRefresh(tv, bus);
    }

    // ── Act 4: combat ───────────────────────────────────────────────
    bus.emit('runner', 'phase', { name: 'combat' });
    const tCombat = Date.now();
    await host.startCombat(ENCOUNTER);
    // Probe: how long until the phones and TV show combat?
    const combatVisible = await pollUntil(async () => phones[0].inCombat(), 30_000);
    bus.emit('runner', 'probe', { name: 'combat-start-to-phone', ms: Date.now() - tCombat, visible: combatVisible });
    if (!combatVisible) bus.emit('runner', 'issue', { name: 'combat-not-visible-on-phone' });
    const tvCombat = await pollUntil(() => tv.hasInitiative(), 15_000);
    if (!tvCombat) bus.emit('runner', 'issue', { name: 'combat-not-visible-on-tv' });
    await tv.screenshot('combat-start');
    for (const phone of phones) await phone.screenshot('combat-start');

    let offlineChaosDone = false;
    let turns = 0;
    let stalls = 0;
    while (turns < cfg.maxCombatTurns) {
      // Whose turn? Poll the phones for the turn badge like players watching for it
      let current: PhoneActor | null = null;
      const found = await pollUntil(async () => {
        for (const p of phones) {
          if (await p.isMyTurn().catch(() => false)) { current = p; return true; }
        }
        return false;
      }, 25_000);

      if (!found || !current) {
        // Nobody has the badge — either combat ended or the table is stuck
        const stillFighting = await phones[0].inCombat().catch(() => false);
        if (!stillFighting) break;
        stalls++;
        bus.emit('runner', 'issue', { name: 'combat-turn-stall', stall: stalls, turns });
        if (stalls >= 3) break;
        continue;
      }

      const phone: PhoneActor = current;
      // Chaos: one player walks off mid-combat with the phone in their pocket
      if (cfg.chaos && !offlineChaosDone && turns === 2 && phones.length >= 3) {
        const victim = phones.find((p) => p !== phone);
        if (victim) {
          offlineChaosDone = true;
          await phoneOffline(victim, bus, 12_000);
        }
      }

      await phone.takeCombatTurn();
      turns++;
      if (turns % 4 === 0) await tv.screenshot(`combat-turn-${turns}`);

      const over = await pollUntil(async () => !(await phones[0].inCombat().catch(() => true)), 5_000, 1_000);
      if (over) break;
    }
    bus.emit('runner', 'phase', { name: 'combat-done', turns });
    await tv.screenshot('combat-end');
    for (const phone of phones) await phone.screenshot('combat-end');

    // ── Act 5: wind down ────────────────────────────────────────────
    bus.emit('runner', 'phase', { name: 'wind-down' });
    if (cfg.chaos) await throttlePhone(phones[phones.length - 1], bus, false);
    const scene = await phones[0].latestNarration();
    await phones[0].takeExplorationTurn(scene || 'The battle is over.');
    await host.endSession();
    await sleep(3_000);
    await tv.screenshot('session-end');

    bus.emit('runner', 'phase', { name: 'complete' });
  } finally {
    for (const phone of phones) await phone.stop().catch(() => {});
    await tv.stop().catch(() => {});
    await host.stop().catch(() => {});
  }
}

async function pollUntil(fn: () => Promise<boolean>, timeoutMs: number, pollMs = 500): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await fn().catch(() => false)) return true;
    await sleep(pollMs);
  }
  return false;
}
