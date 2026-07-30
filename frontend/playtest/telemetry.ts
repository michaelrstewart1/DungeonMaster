/** Backend telemetry over SSH — docker stats sampling during the run and
 * docker compose logs collection afterwards, all dropped into the run dir.
 */
import { execFile } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import type { EventBus } from './events';

function ssh(host: string, command: string, timeoutMs = 30_000): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      'ssh',
      ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', host, command],
      { timeout: timeoutMs, maxBuffer: 32 * 1024 * 1024 },
      (err, stdout, stderr) => (err ? reject(new Error(`${err.message}\n${stderr}`)) : resolve(stdout)),
    );
  });
}

export class BackendTelemetry {
  private timer: ReturnType<typeof setInterval> | null = null;
  private startedAtIso = '';
  private available = false;

  constructor(
    private host: string,
    private runDir: string,
    private bus: EventBus,
    private enabled: boolean,
  ) {}

  async start(): Promise<void> {
    if (!this.enabled) return;
    this.startedAtIso = new Date().toISOString();
    try {
      await ssh(this.host, 'echo ok');
      this.available = true;
    } catch (err) {
      this.bus.emit('backend', 'telemetry', { state: 'unavailable', error: String(err) });
      return;
    }
    this.bus.emit('backend', 'telemetry', { state: 'started' });
    this.timer = setInterval(() => void this.sample(), 15_000);
    void this.sample();
  }

  private async sample(): Promise<void> {
    try {
      const out = await ssh(
        this.host,
        `docker stats --no-stream --format '{{.Name}} {{.CPUPerc}} {{.MemUsage}}'`,
      );
      for (const line of out.trim().split('\n').filter(Boolean)) {
        const [name, cpu, ...mem] = line.split(' ');
        this.bus.emit('backend', 'stats', { container: name, cpu, mem: mem.join(' ') });
      }
    } catch (err) {
      this.bus.emit('backend', 'stats', { error: String(err) });
    }
  }

  /** Stop sampling and collect backend logs covering the run window. */
  async stop(): Promise<void> {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    if (!this.available) return;
    try {
      const logs = await ssh(
        this.host,
        `cd ~/DungeonMaster && docker compose logs --no-color --since '${this.startedAtIso}' backend`,
        60_000,
      );
      fs.writeFileSync(path.join(this.runDir, 'backend.log'), logs);
      this.bus.emit('backend', 'telemetry', { state: 'logs-collected', bytes: logs.length });
    } catch (err) {
      this.bus.emit('backend', 'telemetry', { state: 'log-collection-failed', error: String(err) });
    }
  }
}
