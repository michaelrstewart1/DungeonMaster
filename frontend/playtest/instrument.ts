/** Per-page instrumentation — console, errors, HTTP timing, WS frames,
 * screenshots. Wire this BEFORE the first page.goto().
 */
import * as fs from 'fs';
import * as path from 'path';
import type { Page } from 'playwright-core';
import type { EventBus } from './events';

const MAX_PAYLOAD = 2000;

function trunc(s: string): string {
  return s.length > MAX_PAYLOAD ? s.slice(0, MAX_PAYLOAD) + `…(+${s.length - MAX_PAYLOAD})` : s;
}

/** Extract the `type` field from a WS JSON payload without failing on binary. */
function wsType(payload: string | Buffer): string {
  if (typeof payload !== 'string') return '(binary)';
  try {
    const parsed = JSON.parse(payload);
    return typeof parsed?.type === 'string' ? parsed.type : '(untyped)';
  } catch {
    return '(unparsed)';
  }
}

export function instrumentPage(page: Page, actor: string, bus: EventBus): void {
  page.on('console', (msg) => {
    const level = msg.type();
    if (level === 'error' || level === 'warning') {
      bus.emit(actor, 'console', { level, text: trunc(msg.text()) });
    }
  });

  page.on('pageerror', (err) => {
    bus.emit(actor, 'pageerror', { message: trunc(String(err.message)), stack: trunc(String(err.stack || '')) });
  });

  page.on('crash', () => bus.emit(actor, 'crash', {}));

  page.on('requestfailed', (req) => {
    // Ignore aborted fetches during navigation; record real failures
    bus.emit(actor, 'http:failed', {
      method: req.method(),
      url: req.url(),
      failure: req.failure()?.errorText,
    });
  });

  page.on('requestfinished', async (req) => {
    const url = req.url();
    // Only record API traffic — static assets would swamp the log
    if (!url.includes('/api/')) return;
    try {
      const res = await req.response();
      const timing = req.timing();
      const durationMs = timing.responseEnd >= 0 ? Math.round(timing.responseEnd) : null;
      bus.emit(actor, 'http', {
        method: req.method(),
        path: new URL(url).pathname + (new URL(url).search || ''),
        status: res?.status(),
        durationMs,
        serverMs: res ? parseFloat(res.headers()['x-process-time'] || '') * 1000 || null : null,
      });
    } catch {
      /* response evicted */
    }
  });

  page.on('websocket', (ws) => {
    bus.emit(actor, 'ws:open', { url: ws.url() });
    ws.on('framesent', (frame) => {
      bus.emit(actor, 'ws:sent', { wsType: wsType(frame.payload), payload: trunc(String(frame.payload)) });
    });
    ws.on('framereceived', (frame) => {
      bus.emit(actor, 'ws:recv', { wsType: wsType(frame.payload), payload: trunc(String(frame.payload)) });
    });
    ws.on('close', () => bus.emit(actor, 'ws:close', { url: ws.url() }));
    ws.on('socketerror', (err) => bus.emit(actor, 'ws:error', { error: trunc(String(err)) }));
  });
}

export class ScreenshotTaker {
  private dir: string;
  private n = 0;

  constructor(runDir: string) {
    this.dir = path.join(runDir, 'screenshots');
    fs.mkdirSync(this.dir, { recursive: true });
  }

  /** Screenshot a scenario beat. Never throws — a dead page shouldn't kill the run. */
  async beat(page: Page, actor: string, name: string, bus: EventBus): Promise<void> {
    const file = `${String(this.n++).padStart(3, '0')}-${actor}-${name}.png`;
    try {
      await page.screenshot({ path: path.join(this.dir, file), timeout: 10_000 });
      bus.emit(actor, 'beat', { name, screenshot: file });
    } catch (err) {
      bus.emit(actor, 'beat', { name, screenshot: null, error: String(err) });
    }
  }
}
