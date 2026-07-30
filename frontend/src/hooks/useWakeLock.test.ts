/** useWakeLock — screen wake lock acquisition and re-acquisition. */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useWakeLock } from './useWakeLock';

describe('useWakeLock', () => {
  let release: ReturnType<typeof vi.fn>;
  let request: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    release = vi.fn().mockResolvedValue(undefined);
    request = vi.fn().mockResolvedValue({ release });
    Object.defineProperty(navigator, 'wakeLock', {
      value: { request },
      configurable: true,
    });
  });

  afterEach(() => {
    // @ts-expect-error cleanup test shim
    delete navigator.wakeLock;
  });

  it('requests a screen wake lock on mount', async () => {
    renderHook(() => useWakeLock());
    await vi.waitFor(() => expect(request).toHaveBeenCalledWith('screen'));
  });

  it('releases the lock on unmount', async () => {
    const { unmount } = renderHook(() => useWakeLock());
    await vi.waitFor(() => expect(request).toHaveBeenCalled());
    unmount();
    await vi.waitFor(() => expect(release).toHaveBeenCalled());
  });

  it('re-acquires when the page becomes visible again', async () => {
    renderHook(() => useWakeLock());
    await vi.waitFor(() => expect(request).toHaveBeenCalledTimes(1));

    document.dispatchEvent(new Event('visibilitychange'));
    await vi.waitFor(() => expect(request).toHaveBeenCalledTimes(2));
  });

  it('does nothing when disabled', () => {
    renderHook(() => useWakeLock(false));
    expect(request).not.toHaveBeenCalled();
  });

  it('no-ops gracefully when the API is unsupported', () => {
    // @ts-expect-error simulate unsupported browser
    delete navigator.wakeLock;
    expect(() => renderHook(() => useWakeLock())).not.toThrow();
  });
});
