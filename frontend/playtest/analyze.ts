/** Post-run analyzer — turns events.jsonl + backend.log into report.md:
 * timeline, latency percentiles, error inventory, WS reconnect map, and
 * gap-detection heuristics with a prioritized issues list.
 *
 * Also runnable standalone:  npx tsx playtest/analyze.ts <runDir>
 */
import * as fs from 'fs';
import * as path from 'path';
import type { PlaytestEvent } from './events';

interface Issue {
  severity: 'high' | 'medium' | 'low';
  title: string;
  detail: string;
}

function pct(sorted: number[], p: number): number {
  if (!sorted.length) return 0;
  const idx = Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length));
  return sorted[idx];
}

function fmtMs(ms: number): string {
  return ms >= 10_000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`;
}

function loadEvents(runDir: string): PlaytestEvent[] {
  const file = path.join(runDir, 'events.jsonl');
  if (!fs.existsSync(file)) return [];
  return fs.readFileSync(file, 'utf-8')
    .split('\n')
    .filter(Boolean)
    .map((l) => {
      try { return JSON.parse(l) as PlaytestEvent; } catch { return null; }
    })
    .filter((e): e is PlaytestEvent => e !== null);
}

export async function analyzeRun(runDir: string): Promise<number> {
  const events = loadEvents(runDir);
  const issues: Issue[] = [];
  const lines: string[] = [];
  const t0 = events.length ? events[0].t : Date.now();

  lines.push(`# Playtest Report`);
  lines.push('');
  const meta = fs.existsSync(path.join(runDir, 'meta.json'))
    ? JSON.parse(fs.readFileSync(path.join(runDir, 'meta.json'), 'utf-8'))
    : {};
  lines.push(`- **Run**: ${path.basename(runDir)}`);
  lines.push(`- **Target**: ${meta.baseUrl || '?'} · players=${meta.players ?? '?'} · chaos=${meta.chaos ?? '?'} · llm=${meta.llmBrains ?? '?'}`);
  const durMs = events.length ? events[events.length - 1].t - t0 : 0;
  lines.push(`- **Duration**: ${(durMs / 60000).toFixed(1)} min · ${events.length} events`);
  const runEnd = events.find((e) => e.type === 'run:end');
  lines.push(`- **Outcome**: ${runEnd?.data.ok ? '✅ scenario completed' : `❌ scenario aborted — ${String(runEnd?.data.error || 'unknown').split('\n')[0]}`}`);
  lines.push('');

  if (!runEnd?.data.ok) {
    issues.push({ severity: 'high', title: 'Scenario did not complete', detail: String(runEnd?.data.error || 'run:end missing') });
  }

  // ── Phase timeline ────────────────────────────────────────────────
  lines.push(`## Timeline`);
  lines.push('');
  lines.push('| t+ | phase/beat | actor | detail |');
  lines.push('|----|-----------|-------|--------|');
  for (const ev of events) {
    if (ev.type === 'phase' || ev.type === 'chaos' || ev.type === 'run:timeout') {
      const detail = Object.entries(ev.data).filter(([k]) => k !== 'seq').map(([k, v]) => `${k}=${v}`).join(' ');
      lines.push(`| ${fmtMs(ev.t - t0)} | ${ev.type}:${ev.data.name ?? ''} | ${ev.actor} | ${detail} |`);
    }
  }
  lines.push('');

  // ── Latency probes ────────────────────────────────────────────────
  lines.push(`## Latency`);
  lines.push('');
  const probes = events.filter((e) => e.type === 'probe');
  const byName = new Map<string, number[]>();
  for (const p of probes) {
    const name = String(p.data.name);
    const ms = Number(p.data.ms);
    if (!Number.isFinite(ms)) continue;
    if (!byName.has(name)) byName.set(name, []);
    byName.get(name)!.push(ms);
  }
  lines.push('| interaction | n | p50 | p90 | max |');
  lines.push('|-------------|---|-----|-----|-----|');
  for (const [name, arr] of byName) {
    const sorted = [...arr].sort((a, b) => a - b);
    lines.push(`| ${name} | ${arr.length} | ${fmtMs(pct(sorted, 50))} | ${fmtMs(pct(sorted, 90))} | ${fmtMs(sorted[sorted.length - 1])} |`);
  }
  lines.push('');

  const narr = byName.get('action-to-tv-narration') || [];
  const slowNarr = narr.filter((ms) => ms > 45_000);
  if (slowNarr.length) {
    issues.push({
      severity: 'medium',
      title: `Slow DM responses (${slowNarr.length}/${narr.length} actions >45s to reach the TV)`,
      detail: `Worst: ${fmtMs(Math.max(...slowNarr))}. Players lose engagement past ~30s. Check LLM provider latency / fallback.`,
    });
  }

  // Failed recovery probes are high-severity — real players would be locked out
  for (const p of probes) {
    if ((p.data.recovered === false) || (p.data.visible === false) || (p.data.updated === false)) {
      issues.push({
        severity: 'high',
        title: `Probe failed: ${p.data.name} (${p.actor})`,
        detail: JSON.stringify(p.data),
      });
    }
  }

  // ── HTTP health ───────────────────────────────────────────────────
  lines.push(`## HTTP`);
  lines.push('');
  const https = events.filter((e) => e.type === 'http');
  const errors5xx = https.filter((e) => Number(e.data.status) >= 500);
  const errors4xx = https.filter((e) => Number(e.data.status) >= 400 && Number(e.data.status) < 500);
  const durations = https.map((e) => Number(e.data.durationMs)).filter(Number.isFinite).sort((a, b) => a - b);
  lines.push(`- ${https.length} API requests · p50 ${fmtMs(pct(durations, 50))} · p90 ${fmtMs(pct(durations, 90))} · max ${fmtMs(durations[durations.length - 1] || 0)}`);
  lines.push(`- 5xx: ${errors5xx.length} · 4xx: ${errors4xx.length} · network failures: ${events.filter((e) => e.type === 'http:failed').length}`);
  lines.push('');
  const errSample = [...errors5xx, ...errors4xx].slice(0, 15);
  if (errSample.length) {
    lines.push('| status | method | path | actor |');
    lines.push('|--------|--------|------|-------|');
    for (const e of errSample) lines.push(`| ${e.data.status} | ${e.data.method} | ${e.data.path} | ${e.actor} |`);
    lines.push('');
  }
  if (errors5xx.length) {
    issues.push({ severity: 'high', title: `${errors5xx.length} server errors (5xx) during play`, detail: errors5xx.slice(0, 5).map((e) => `${e.data.method} ${e.data.path} → ${e.data.status}`).join('; ') });
  }
  const failedReq = events.filter((e) => e.type === 'http:failed' && !String(e.data.failure).includes('ERR_ABORTED'));
  const offlineWindow = new Set<string>();
  for (const c of events.filter((e) => e.type === 'chaos' && e.data.name === 'offline')) offlineWindow.add(c.actor);
  const unexplainedFails = failedReq.filter((e) => !offlineWindow.has(e.actor));
  if (unexplainedFails.length > 3) {
    issues.push({ severity: 'medium', title: `${unexplainedFails.length} failed requests outside chaos windows`, detail: unexplainedFails.slice(0, 5).map((e) => `${e.actor}: ${e.data.method} ${String(e.data.url).slice(0, 80)} (${e.data.failure})`).join('; ') });
  }

  // ── WebSocket health ──────────────────────────────────────────────
  lines.push(`## WebSocket`);
  lines.push('');
  const wsOpens = events.filter((e) => e.type === 'ws:open');
  const wsCloses = events.filter((e) => e.type === 'ws:close');
  const wsErrors = events.filter((e) => e.type === 'ws:error');
  const opensByActor = new Map<string, number>();
  for (const e of wsOpens) opensByActor.set(e.actor, (opensByActor.get(e.actor) || 0) + 1);
  lines.push('| actor | opens | closes | errors |');
  lines.push('|-------|-------|--------|--------|');
  for (const [actor, opens] of opensByActor) {
    lines.push(`| ${actor} | ${opens} | ${wsCloses.filter((e) => e.actor === actor).length} | ${wsErrors.filter((e) => e.actor === actor).length} |`);
  }
  lines.push('');
  // Excessive reconnects outside chaos = flaky WS layer
  for (const [actor, opens] of opensByActor) {
    const chaosHit = events.some((e) => e.type === 'chaos' && (e.actor === actor || e.data.name === 'tv-refresh'));
    // each page load opens up to 2 sockets (game + audio); refreshes double it
    const allowance = chaosHit ? 8 : 4;
    if (opens > allowance) {
      issues.push({ severity: 'medium', title: `${actor}: ${opens} WS connections (reconnect churn)`, detail: 'More sockets opened than page-lifecycle explains — check reconnect backoff.' });
    }
  }

  // Unhandled/unknown WS message types reaching clients
  const knownTypes = new Set(['(binary)', '(unparsed)']);
  const wsRecvTypes = new Map<string, number>();
  for (const e of events.filter((ev) => ev.type === 'ws:recv')) {
    const t = String(e.data.wsType);
    wsRecvTypes.set(t, (wsRecvTypes.get(t) || 0) + 1);
  }
  lines.push(`WS message types received: ${[...wsRecvTypes.entries()].map(([t, n]) => `${t}×${n}`).join(', ') || 'none'}`);
  lines.push('');
  if (wsRecvTypes.get('(untyped)')) {
    issues.push({ severity: 'low', title: `${wsRecvTypes.get('(untyped)')} untyped WS messages`, detail: 'Server sent JSON without a type field — clients cannot route these.' });
  }

  // ── Console / page errors ─────────────────────────────────────────
  lines.push(`## Client errors`);
  lines.push('');
  const pageErrors = events.filter((e) => e.type === 'pageerror');
  const consoleErrors = events.filter((e) => e.type === 'console' && e.data.level === 'error');
  const crashes = events.filter((e) => e.type === 'crash');
  lines.push(`- Page errors: ${pageErrors.length} · console errors: ${consoleErrors.length} · crashes: ${crashes.length}`);
  const dedup = new Map<string, { n: number; actors: Set<string> }>();
  for (const e of [...pageErrors, ...consoleErrors]) {
    const key = String(e.data.message || e.data.text).slice(0, 160);
    if (!dedup.has(key)) dedup.set(key, { n: 0, actors: new Set() });
    const d = dedup.get(key)!;
    d.n++;
    d.actors.add(e.actor);
  }
  for (const [msg, d] of [...dedup.entries()].slice(0, 20)) {
    lines.push(`  - \`${msg.replace(/`/g, "'")}\` ×${d.n} (${[...d.actors].join(', ')})`);
  }
  lines.push('');
  if (crashes.length) issues.push({ severity: 'high', title: `${crashes.length} page crash(es)`, detail: crashes.map((e) => e.actor).join(', ') });
  if (pageErrors.length) {
    issues.push({ severity: 'high', title: `${pageErrors.length} uncaught page errors`, detail: [...dedup.keys()][0] || '' });
  }

  // ── Errors emitted by actors (dead-ends, unavailable buttons) ─────
  const actorErrors = events.filter((e) => e.type === 'error');
  for (const e of actorErrors) {
    issues.push({ severity: 'medium', title: `${e.actor}: ${e.data.where}`, detail: String(e.data.error) });
  }

  // ── Runner-detected gaps ──────────────────────────────────────────
  for (const e of events.filter((ev) => ev.type === 'issue')) {
    issues.push({
      severity: e.data.name === 'combat-turn-stall' || String(e.data.name).includes('not-visible') ? 'high' : 'medium',
      title: `Gap: ${e.data.name}`,
      detail: Object.entries(e.data).filter(([k]) => !['seq', 'name'].includes(k)).map(([k, v]) => `${k}=${v}`).join(' '),
    });
  }

  // ── LLM brain health ──────────────────────────────────────────────
  const brains = events.filter((e) => e.type === 'brain');
  const brainFails = brains.filter((e) => e.data.source === 'llm-failed');
  lines.push(`## Player brains`);
  lines.push('');
  lines.push(`- Decisions: ${brains.length} (llm=${brains.filter((e) => e.data.source === 'llm').length}, playbook=${brains.filter((e) => e.data.source === 'playbook').length}, failed=${brainFails.length})`);
  const brainMs = brains.filter((e) => e.data.source === 'llm').map((e) => Number(e.data.ms)).sort((a, b) => a - b);
  if (brainMs.length) lines.push(`- LLM decision time: p50 ${fmtMs(pct(brainMs, 50))} · max ${fmtMs(brainMs[brainMs.length - 1])}`);
  lines.push('');

  // ── Backend telemetry ─────────────────────────────────────────────
  const backendLog = path.join(runDir, 'backend.log');
  if (fs.existsSync(backendLog)) {
    const log = fs.readFileSync(backendLog, 'utf-8');
    const logLines = log.split('\n');
    const errLines = logLines.filter((l) => /ERROR|CRITICAL|Traceback/.test(l));
    const warnLines = logLines.filter((l) => /WARNING/.test(l));
    lines.push(`## Backend`);
    lines.push('');
    lines.push(`- Log lines: ${logLines.length} · errors: ${errLines.length} · warnings: ${warnLines.length}`);
    for (const l of errLines.slice(0, 10)) lines.push(`  - \`${l.trim().slice(0, 180).replace(/`/g, "'")}\``);
    const stats = events.filter((e) => e.type === 'stats' && e.data.container);
    const backendStats = stats.filter((e) => String(e.data.container).includes('backend'));
    if (backendStats.length) {
      const cpus = backendStats.map((e) => parseFloat(String(e.data.cpu))).filter(Number.isFinite);
      lines.push(`- Backend CPU: avg ${(cpus.reduce((a, b) => a + b, 0) / cpus.length).toFixed(1)}% · peak ${Math.max(...cpus).toFixed(1)}%`);
    }
    lines.push('');
    if (errLines.length) {
      issues.push({ severity: 'high', title: `${errLines.length} backend error log lines during the run`, detail: errLines[0]?.trim().slice(0, 160) || '' });
    }
  }

  // ── Issues (prioritized) ──────────────────────────────────────────
  const order = { high: 0, medium: 1, low: 2 } as const;
  issues.sort((a, b) => order[a.severity] - order[b.severity]);
  lines.push(`## Issues found (${issues.length})`);
  lines.push('');
  if (!issues.length) lines.push('None — clean run. 🎉');
  for (const [i, issue] of issues.entries()) {
    lines.push(`${i + 1}. **[${issue.severity.toUpperCase()}] ${issue.title}**`);
    lines.push(`   ${issue.detail}`);
  }
  lines.push('');

  // ── Screenshots ───────────────────────────────────────────────────
  const shotDir = path.join(runDir, 'screenshots');
  if (fs.existsSync(shotDir)) {
    lines.push(`## Screenshots`);
    lines.push('');
    for (const f of fs.readdirSync(shotDir).sort()) lines.push(`- [${f}](screenshots/${f})`);
    lines.push('');
  }

  fs.writeFileSync(path.join(runDir, 'report.md'), lines.join('\n'));
  return issues.length;
}

// Standalone: npx tsx playtest/analyze.ts <runDir>
const invokedDirectly = process.argv[1] && /analyze\.(ts|js)$/.test(process.argv[1]);
if (invokedDirectly) {
  const dir = process.argv[2];
  if (!dir) {
    console.error('usage: npx tsx playtest/analyze.ts <runDir>');
    process.exit(2);
  }
  analyzeRun(path.resolve(dir)).then((n) => {
    console.log(`report written · ${n} issues`);
  });
}
