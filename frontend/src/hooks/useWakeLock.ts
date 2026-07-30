/**
 * Screen Wake Lock — keeps a phone/TV screen awake while a game screen is
 * open. Between turns players may not touch their phone for minutes; without
 * this the screen times out, the OS freezes the tab, and the WS drops.
 *
 * The lock is automatically released by the browser whenever the page is
 * hidden (user locks the phone anyway, switches apps), so it is re-acquired
 * on every return to visibility. No-ops gracefully where unsupported
 * (older iOS Safari) — reconnect/resync remains the safety net there.
 */
import { useEffect } from 'react';

interface WakeLockSentinelLike {
  release: () => Promise<void>;
  released?: boolean;
}

export function useWakeLock(enabled: boolean = true): void {
  useEffect(() => {
    if (!enabled) return;
    const wakeLock = (navigator as Navigator & {
      wakeLock?: { request: (type: 'screen') => Promise<WakeLockSentinelLike> };
    }).wakeLock;
    if (!wakeLock) return;

    let sentinel: WakeLockSentinelLike | null = null;
    let disposed = false;

    const acquire = async () => {
      try {
        sentinel = await wakeLock.request('screen');
        // If unmount raced the request, release immediately.
        if (disposed) await sentinel.release();
      } catch {
        // Denied (low battery mode, permissions) — non-fatal.
        sentinel = null;
      }
    };

    const onVisibility = () => {
      if (!document.hidden) acquire();
    };

    acquire();
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      disposed = true;
      document.removeEventListener('visibilitychange', onVisibility);
      sentinel?.release().catch(() => {});
    };
  }, [enabled]);
}
