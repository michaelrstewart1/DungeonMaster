/** Chaos injections — the stuff that actually happens on family game night:
 * someone's phone drops off wifi, someone refreshes mid-turn, the network
 * crawls. All flag-gated and logged as chaos events for the analyzer.
 */
import type { EventBus } from './events';
import type { PhoneActor, TVActor } from './actors';
import { sleep } from './human';

/** Phone loses connectivity for `offlineMs`, then comes back and must recover. */
export async function phoneOffline(phone: PhoneActor, bus: EventBus, offlineMs = 15_000): Promise<void> {
  bus.emit(phone.name, 'chaos', { name: 'offline', state: 'start', offlineMs });
  await phone.context.setOffline(true);
  await sleep(offlineMs);
  await phone.context.setOffline(false);
  bus.emit(phone.name, 'chaos', { name: 'offline', state: 'end' });
  // Give the WS reconnect logic time to do its thing, then verify recovery
  const t0 = Date.now();
  const recovered = await phone.page
    .waitForSelector('.pv-action-input', { timeout: 45_000 })
    .then(() => true)
    .catch(() => false);
  bus.emit(phone.name, 'probe', { name: 'offline-recovery', ms: Date.now() - t0, recovered });
  await phone.screenshot('after-offline-recovery');
}

/** Throttle one phone to lousy 3G via CDP (chromium-only). */
export async function throttlePhone(phone: PhoneActor, bus: EventBus, enable: boolean): Promise<void> {
  try {
    const client = await phone.context.newCDPSession(phone.page);
    await client.send('Network.emulateNetworkConditions', enable
      ? { offline: false, latency: 400, downloadThroughput: (500 * 1024) / 8, uploadThroughput: (250 * 1024) / 8 }
      : { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
    await client.detach().catch(() => {});
    bus.emit(phone.name, 'chaos', { name: '3g-throttle', state: enable ? 'start' : 'end' });
  } catch (err) {
    bus.emit(phone.name, 'chaos', { name: '3g-throttle', state: 'failed', error: String(err) });
  }
}

/** Refresh the phone mid-game — exercises the identity/rejoin resume path. */
export async function phoneRefresh(phone: PhoneActor, bus: EventBus): Promise<void> {
  bus.emit(phone.name, 'chaos', { name: 'mid-game-refresh', state: 'start' });
  const t0 = Date.now();
  await phone.page.reload({ waitUntil: 'domcontentloaded' });
  const recovered = await phone.page
    .waitForSelector('.pv-action-input', { timeout: 45_000 })
    .then(() => true)
    .catch(() => false);
  bus.emit(phone.name, 'probe', { name: 'refresh-recovery', ms: Date.now() - t0, recovered });
  await phone.screenshot('after-refresh');
}

/** Refresh the TV during play — the DM display must rebuild its state. */
export async function tvRefresh(tv: TVActor, bus: EventBus): Promise<void> {
  bus.emit(TVActorName(), 'chaos', { name: 'tv-refresh', state: 'start' });
  const t0 = Date.now();
  await tv.page.reload({ waitUntil: 'domcontentloaded' });
  const recovered = await tv.page
    .waitForSelector('.dm-display', { timeout: 45_000 })
    .then(() => true)
    .catch(() => false);
  bus.emit(TVActorName(), 'probe', { name: 'tv-refresh-recovery', ms: Date.now() - t0, recovered });
  await tv.screenshot('after-tv-refresh');
}

function TVActorName(): string {
  return 'tv';
}
