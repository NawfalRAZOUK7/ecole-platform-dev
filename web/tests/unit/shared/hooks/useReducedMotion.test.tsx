/**
 * Tests for src/shared/hooks/useReducedMotion.ts
 * Covers:
 *  - initial state from window.matchMedia
 *  - reacts to media query change events
 *  - cleans up the listener on unmount
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useReducedMotion } from '@/shared/hooks/useReducedMotion';

interface MockMediaQueryList {
  matches: boolean;
  listeners: Map<string, (event: MediaQueryListEvent) => void>;
  addEventListener: (name: string, cb: (event: MediaQueryListEvent) => void) => void;
  removeEventListener: (name: string, cb: (event: MediaQueryListEvent) => void) => void;
  dispatch: (matches: boolean) => void;
}

function createMockMediaQuery(initial: boolean): MockMediaQueryList {
  const listeners = new Map<string, (event: MediaQueryListEvent) => void>();
  return {
    matches: initial,
    listeners,
    addEventListener(name, cb) {
      listeners.set(name, cb);
    },
    removeEventListener(name) {
      listeners.delete(name);
    },
    dispatch(matches) {
      this.matches = matches;
      listeners.get('change')?.({ matches } as MediaQueryListEvent);
    },
  };
}

describe('shared/hooks/useReducedMotion', () => {
  let mockMql: MockMediaQueryList;
  let originalMatchMedia: typeof window.matchMedia;

  beforeEach(() => {
    originalMatchMedia = window.matchMedia;
    mockMql = createMockMediaQuery(false);
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      writable: true,
      value: vi.fn(() => mockMql),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      writable: true,
      value: originalMatchMedia,
    });
  });

  it('returns false when no reduced motion is preferred', () => {
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);
  });

  it('returns true when the media query initially matches', () => {
    mockMql.matches = true;
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(true);
  });

  it('reacts to media query change events', () => {
    const { result } = renderHook(() => useReducedMotion());
    expect(result.current).toBe(false);

    act(() => {
      mockMql.dispatch(true);
    });
    expect(result.current).toBe(true);

    act(() => {
      mockMql.dispatch(false);
    });
    expect(result.current).toBe(false);
  });

  it('removes the change listener on unmount', () => {
    const { unmount } = renderHook(() => useReducedMotion());
    expect(mockMql.listeners.has('change')).toBe(true);
    unmount();
    expect(mockMql.listeners.has('change')).toBe(false);
  });

  it('uses the correct media query string', () => {
    renderHook(() => useReducedMotion());
    expect(window.matchMedia).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)');
  });
});
