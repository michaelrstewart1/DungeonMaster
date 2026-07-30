/** Playtest configuration — env-driven, with VM deployment defaults. */
import * as path from 'path';

export interface PlaytestConfig {
  /** Frontend base URL (the thing humans point their phones at). */
  baseUrl: string;
  /** Ollama endpoint used for LLM player brains. */
  ollamaUrl: string;
  ollamaModel: string;
  /** Number of simulated phone players (1-4). */
  players: number;
  /** Exploration rounds before combat starts. */
  explorationRounds: number;
  /** Max combat player-turns before we bail (safety valve). */
  maxCombatTurns: number;
  /** Enable chaos injections (offline phone, throttling, refreshes). */
  chaos: boolean;
  /** Use LLM brains (falls back to scripted playbooks on failure). */
  llmBrains: boolean;
  /** Collect backend telemetry over SSH (docker logs/stats). */
  backendTelemetry: boolean;
  /** SSH destination for backend telemetry, e.g. dungeon@192.168.1.94 */
  sshHost: string;
  /** Run with visible browser windows. */
  headed: boolean;
  /** Output directory for this run. */
  runDir: string;
  /** Global timeout for a whole run, ms. */
  runTimeoutMs: number;
}

function envBool(name: string, def: boolean): boolean {
  const v = process.env[name];
  if (v === undefined || v === '') return def;
  return ['1', 'true', 'yes', 'on'].includes(v.toLowerCase());
}

function envInt(name: string, def: number): number {
  const v = parseInt(process.env[name] || '', 10);
  return Number.isFinite(v) ? v : def;
}

export function loadConfig(): PlaytestConfig {
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const runDir = process.env.PLAYTEST_RUN_DIR
    || path.join(process.cwd(), '..', 'playtest-runs', ts);
  return {
    baseUrl: process.env.PLAYTEST_BASE_URL || 'http://192.168.1.94',
    ollamaUrl: process.env.PLAYTEST_OLLAMA_URL || 'http://192.168.1.94:11434',
    ollamaModel: process.env.PLAYTEST_OLLAMA_MODEL || 'llama3.1:8b',
    players: Math.min(4, Math.max(1, envInt('PLAYTEST_PLAYERS', 4))),
    explorationRounds: envInt('PLAYTEST_EXPLORATION_ROUNDS', 2),
    maxCombatTurns: envInt('PLAYTEST_MAX_COMBAT_TURNS', 24),
    chaos: envBool('PLAYTEST_CHAOS', true),
    llmBrains: envBool('PLAYTEST_LLM', true),
    backendTelemetry: envBool('PLAYTEST_TELEMETRY', true),
    sshHost: process.env.PLAYTEST_SSH_HOST || 'dungeon@192.168.1.94',
    headed: envBool('PLAYTEST_HEADED', false),
    runDir,
    runTimeoutMs: envInt('PLAYTEST_TIMEOUT_MS', 25 * 60 * 1000),
  };
}
