/** Playtest entry point.
 *
 *   npx tsx playtest/run.ts            # full game night vs the deployed VM
 *   PLAYTEST_BASE_URL=http://localhost:5173 npx tsx playtest/run.ts
 *
 * Produces playtest-runs/<timestamp>/ with events.jsonl, screenshots/,
 * traces, backend.log, and report.md (via analyze.ts).
 */
import { chromium } from 'playwright-core';
import * as fs from 'fs';
import * as path from 'path';
import { loadConfig } from './config';
import { EventBus } from './events';
import { runGameNight } from './scenario';
import { BackendTelemetry } from './telemetry';
import { analyzeRun } from './analyze';

async function main(): Promise<number> {
  const cfg = loadConfig();
  fs.mkdirSync(cfg.runDir, { recursive: true });
  fs.writeFileSync(path.join(cfg.runDir, 'meta.json'), JSON.stringify(cfg, null, 2));
  const bus = new EventBus(cfg.runDir);
  bus.emit('runner', 'run:start', { baseUrl: cfg.baseUrl, players: cfg.players, chaos: cfg.chaos, llm: cfg.llmBrains });
  console.log(`[playtest] run dir: ${cfg.runDir}`);
  console.log(`[playtest] target:  ${cfg.baseUrl} (${cfg.players} players, chaos=${cfg.chaos}, llm=${cfg.llmBrains})`);

  const telemetry = new BackendTelemetry(cfg.sshHost, cfg.runDir, bus, cfg.backendTelemetry);
  await telemetry.start();

  const browser = await chromium.launch({ headless: !cfg.headed });
  let failed = false;
  const killer = setTimeout(() => {
    bus.emit('runner', 'run:timeout', { afterMs: cfg.runTimeoutMs });
    console.error('[playtest] global timeout — aborting');
    void browser.close();
  }, cfg.runTimeoutMs);

  try {
    await runGameNight(browser, cfg, bus);
    bus.emit('runner', 'run:end', { ok: true });
  } catch (err) {
    failed = true;
    bus.emit('runner', 'run:end', { ok: false, error: String(err instanceof Error ? err.stack || err.message : err) });
    console.error('[playtest] scenario failed:', err);
  } finally {
    clearTimeout(killer);
    await browser.close().catch(() => {});
    await telemetry.stop();
    await bus.close();
  }

  console.log('[playtest] analyzing…');
  const issues = await analyzeRun(cfg.runDir);
  console.log(`[playtest] report: ${path.join(cfg.runDir, 'report.md')}`);
  console.log(`[playtest] issues found: ${issues}`);
  return failed ? 1 : 0;
}

main().then((code) => process.exit(code)).catch((err) => {
  console.error(err);
  process.exit(1);
});
