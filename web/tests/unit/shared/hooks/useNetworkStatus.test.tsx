/**
 * Tests for src/shared/hooks/useNetworkStatus.ts
 * Covers:
 *  - initial state from navigator.onLine
 *  - online/offline event reactions
 *  - wasOffline transient flag clears after 3s
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useNetworkStatus } from '@/shared/hooks/useNetworkStatus';

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', {
    configurable: true,
    get: () => value,
  });
}

describe('shared/hooks/useNetworkStatus', () => {
  beforeEach(() => {
    setOnline(true);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns isOnline=true and wasOffline=false on initial render when navigator is online', () => {
    const { result } = renderHook(() => useNetworkStatus());
    expect(result.current.isOnline).toBe(true);
    expect(result.current.wasOffline).toBe(false);
  });

  it('switches to isOnline=false on offline event', () => {
    const { result } = renderHook(() => useNetworkStatus());

    act(() => {
      window.dispatchEvent(new Event('offline'));
    });

    expect(result.current.isOnline).toBe(false);
    expect(result.current.wasOffline).toBe(false);
  });

  it('switches to isOnline=true and wasOffline=true on online event', () => {
    const { result } = renderHook(() => useNetworkStatus());

    act(() => {
      window.dispatchEvent(new Event('offline'));
    });
    act(() => {
      window.dispatchEvent(new Event('online'));
    });

    expect(result.current.isOnline).toBe(true);
    expect(result.current.wasOffline).toBe(true);
  });

  it('clears wasOffline after the 3s reconnect window', () => {
    const { result } = renderHook(() => useNetworkStatus());

    act(() => {
      window.dispatchEvent(new Event('offline'));
    });
    act(() => {
      window.dispatchEvent(new Event('online'));
    });
    expect(result.current.wasOffline).toBe(true);

    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(result.current.wasOffline).toBe(false);
  });

  it('clears the reconnect timer when the user goes offline again before 3s', () => {
    const { result } = renderHook(() => useNetworkStatus());

    act(() => {
      window.dispatchEvent(new Event('offline'));
    });
    act(() => {
      window.dispatchEvent(new Event('online'));
    });
    expect(result.current.wasOffline).toBe(true);

    // Go offline again before the 3s timer fires
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });
    // Advance well past 3s — wasOffline should NOT flicker back to true
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current.isOnline).toBe(false);
    expect(result.current.wasOffline).toBe(false);
  });

  it('removes window listeners on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const { unmount } = renderHook(() => useNetworkStatus());

    unmount();

    expect(removeSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith('offline', expect.any(Function));
  });
});
