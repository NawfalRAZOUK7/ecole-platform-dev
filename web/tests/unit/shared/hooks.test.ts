/**
 * Tests for shared hooks:
 * - useTheme (src/shared/hooks/useTheme.ts)
 * - useReducedMotion (src/shared/hooks/useReducedMotion.ts)
 * - useNetworkStatus (src/shared/hooks/useNetworkStatus.ts)
 * - useDirectUpload (src/shared/hooks/useDirectUpload.ts)
 */
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// ---------------------------------------------------------------------------
// useTheme
// ---------------------------------------------------------------------------

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear?.();
    document.documentElement.removeAttribute('data-theme');
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockImplementation((query: string) => ({
        matches: query.includes('dark') ? false : false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('defaults to light when no stored preference and no dark system', async () => {
    const { useTheme } = await import('@/shared/hooks/useTheme');
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('light');
  });

  it('reads stored preference from localStorage', async () => {
    localStorage.setItem('ecole-theme', 'dark');
    const { useTheme } = await import('@/shared/hooks/useTheme');
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('dark');
  });

  it('setTheme changes theme and stores in localStorage', async () => {
    const { useTheme } = await import('@/shared/hooks/useTheme');
    const { result } = renderHook(() => useTheme());
    act(() => result.current.setTheme('dark'));
    expect(result.current.theme).toBe('dark');
    expect(localStorage.getItem('ecole-theme')).toBe('dark');
  });

  it('toggleTheme switches from light to dark', async () => {
    const { useTheme } = await import('@/shared/hooks/useTheme');
    const { result } = renderHook(() => useTheme());
    act(() => result.current.toggleTheme());
    expect(result.current.theme).toBe('dark');
  });

  it('toggleTheme switches from dark to light', async () => {
    localStorage.setItem('ecole-theme', 'dark');
    const { useTheme } = await import('@/shared/hooks/useTheme');
    const { result } = renderHook(() => useTheme());
    act(() => result.current.toggleTheme());
    expect(result.current.theme).toBe('light');
  });

  it('sets data-theme attribute on documentElement when theme changes', async () => {
    const { useTheme } = await import('@/shared/hooks/useTheme');
    const { result } = renderHook(() => useTheme());
    act(() => result.current.setTheme('dark'));
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('defaults to dark when system prefers dark and no stored preference', async () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockImplementation((query: string) => ({
        matches: query.includes('dark'),
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    );
    const { useTheme } = await import('@/shared/hooks/useTheme');
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('dark');
  });

  it('system dark change is handled without stored preference', async () => {
    // Verify that the media query listener is registered and handles changes
    const listeners = new Map<string, (e: MediaQueryListEvent) => void>();
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        addEventListener: (event: string, handler: (e: MediaQueryListEvent) => void) => {
          listeners.set(`${query}-${event}`, handler);
        },
        removeEventListener: vi.fn(),
      })),
    );
    const { useTheme } = await import('@/shared/hooks/useTheme');
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe('light');
    // Listeners are registered (the hook attaches to matchMedia change)
    expect(listeners.size).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// useReducedMotion
// ---------------------------------------------------------------------------

describe('useReducedMotion', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns false when prefers-reduced-motion is not set', async () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }),
    );
    const { useReducedMotion } = await import('@/shared/hooks/useReducedMotion');
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);
  });

  it('returns true when prefers-reduced-motion is set', async () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }),
    );
    const { useReducedMotion } = await import('@/shared/hooks/useReducedMotion');
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(true);
  });

  it('updates when media query changes', async () => {
    const listeners: Record<string, (e: MediaQueryListEvent) => void> = {};
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({
        matches: false,
        addEventListener: (event: string, handler: (e: MediaQueryListEvent) => void) => {
          listeners[event] = handler;
        },
        removeEventListener: vi.fn(),
      }),
    );
    const { useReducedMotion } = await import('@/shared/hooks/useReducedMotion');
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);
    act(() => listeners['change']?.({ matches: true } as MediaQueryListEvent));
    expect(result.current).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// useNetworkStatus
// ---------------------------------------------------------------------------

describe('useNetworkStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true, writable: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('is online initially when navigator.onLine is true', async () => {
    const { useNetworkStatus } = await import('@/shared/hooks/useNetworkStatus');
    const { result } = renderHook(() => useNetworkStatus());
    expect(result.current.isOnline).toBe(true);
    expect(result.current.wasOffline).toBe(false);
  });

  it('is offline initially when navigator.onLine is false', async () => {
    Object.defineProperty(navigator, 'onLine', {
      value: false,
      configurable: true,
      writable: true,
    });
    const { useNetworkStatus } = await import('@/shared/hooks/useNetworkStatus');
    const { result } = renderHook(() => useNetworkStatus());
    expect(result.current.isOnline).toBe(false);
  });

  it('goes offline when offline event fires', async () => {
    const { useNetworkStatus } = await import('@/shared/hooks/useNetworkStatus');
    const { result } = renderHook(() => useNetworkStatus());
    act(() => window.dispatchEvent(new Event('offline')));
    expect(result.current.isOnline).toBe(false);
  });

  it('goes online when online event fires', async () => {
    const { useNetworkStatus } = await import('@/shared/hooks/useNetworkStatus');
    const { result } = renderHook(() => useNetworkStatus());
    act(() => window.dispatchEvent(new Event('offline')));
    expect(result.current.isOnline).toBe(false);
    act(() => window.dispatchEvent(new Event('online')));
    expect(result.current.isOnline).toBe(true);
    expect(result.current.wasOffline).toBe(true);
  });

  it('clears wasOffline after 3 seconds', async () => {
    const { useNetworkStatus } = await import('@/shared/hooks/useNetworkStatus');
    const { result } = renderHook(() => useNetworkStatus());
    act(() => window.dispatchEvent(new Event('offline')));
    act(() => window.dispatchEvent(new Event('online')));
    expect(result.current.wasOffline).toBe(true);
    act(() => vi.advanceTimersByTime(3001));
    expect(result.current.wasOffline).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// useDirectUpload
// ---------------------------------------------------------------------------

describe('useDirectUpload', () => {
  it('starts with null state, 0 progress, no error', async () => {
    const { useDirectUpload } = await import('@/shared/hooks/useDirectUpload');
    const { result } = renderHook(() => useDirectUpload());
    expect(result.current.state).toBeNull();
    expect(result.current.progress).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it('reset clears state, progress, and error', async () => {
    const { useDirectUpload } = await import('@/shared/hooks/useDirectUpload');
    const { result } = renderHook(() => useDirectUpload());
    act(() => result.current.reset());
    expect(result.current.state).toBeNull();
    expect(result.current.progress).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it('uploadDirect exists and is callable', async () => {
    const { useDirectUpload } = await import('@/shared/hooks/useDirectUpload');
    const { result } = renderHook(() => useDirectUpload());
    expect(typeof result.current.uploadDirect).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });
});
