/** Event bus — every observation from every actor lands in one JSONL file.
 * Post-run analysis (analyze.ts) consumes this file to build the report.
 */
import * as fs from 'fs';
import * as path from 'path';

export interface PlaytestEvent {
  /** epoch ms */
  t: number;
  /** wall-clock ISO for humans */
  iso: string;
  /** which actor observed it: host | tv | phone-<name> | runner | backend */
  actor: string;
  /** event type, e.g. console, http, ws:recv, ws:sent, action, beat, chaos, error, probe */
  type: string;
  data: Record<string, unknown>;
}

export class EventBus {
  private stream: fs.WriteStream;
  private events: PlaytestEvent[] = [];
  private seq = 0;

  constructor(runDir: string) {
    fs.mkdirSync(runDir, { recursive: true });
    this.stream = fs.createWriteStream(path.join(runDir, 'events.jsonl'), { flags: 'a' });
  }

  emit(actor: string, type: string, data: Record<string, unknown> = {}): PlaytestEvent {
    const now = Date.now();
    const ev: PlaytestEvent = { t: now, iso: new Date(now).toISOString(), actor, type, data: { seq: this.seq++, ...data } };
    this.events.push(ev);
    this.stream.write(JSON.stringify(ev) + '\n');
    return ev;
  }

  /** In-memory view for live probes (e.g. waiting for a WS message). */
  all(): readonly PlaytestEvent[] {
    return this.events;
  }

  /** Wait until an event matching the predicate is emitted (or timeout).
   * Scans events emitted after `sinceT`. Returns the event or null. */
  async waitFor(
    predicate: (ev: PlaytestEvent) => boolean,
    opts: { sinceT?: number; timeoutMs?: number; pollMs?: number } = {},
  ): Promise<PlaytestEvent | null> {
    const sinceT = opts.sinceT ?? Date.now();
    const timeoutMs = opts.timeoutMs ?? 30_000;
    const pollMs = opts.pollMs ?? 200;
    const deadline = Date.now() + timeoutMs;
    let scanned = 0;
    while (Date.now() < deadline) {
      for (; scanned < this.events.length; scanned++) {
        const ev = this.events[scanned];
        if (ev.t >= sinceT && predicate(ev)) return ev;
      }
      await new Promise((r) => setTimeout(r, pollMs));
    }
    return null;
  }

  async close(): Promise<void> {
    await new Promise<void>((resolve) => this.stream.end(() => resolve()));
  }
}
