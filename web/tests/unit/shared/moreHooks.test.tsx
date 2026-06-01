/**
 * Tests for remaining uncovered hooks:
 * - useAgeTheme
 * - useFocusManagement
 */
import { renderHook, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { type ReactNode } from 'react';
import { useAgeTheme } from '@/shared/hooks/useAgeTheme';
import { useFocusManagement } from '@/shared/hooks/useFocusManagement';

// ---------------------------------------------------------------------------
// useAgeTheme
// ---------------------------------------------------------------------------

describe('useAgeTheme', () => {
  afterEach(() => {
    document.documentElement.removeAttribute('data-age-tier');
  });

  it('returns "primaire" as default when no dateOfBirth', () => {
    const { result } = renderHook(() => useAgeTheme(null));
    expect(result.current).toBe('primaire');
  });

  it('returns "primaire" as default when dateOfBirth is undefined', () => {
    const { result } = renderHook(() => useAgeTheme(undefined));
    expect(result.current).toBe('primaire');
  });

  it('returns "maternelle" for age <= 5', () => {
    const today = new Date();
    const dob = new Date(today.getFullYear() - 4, today.getMonth(), today.getDate());
    const dobStr = dob.toISOString().split('T')[0];
    const { result } = renderHook(() => useAgeTheme(dobStr));
    expect(result.current).toBe('maternelle');
  });

  it('returns "primaire" for age 6-9', () => {
    const today = new Date();
    const dob = new Date(today.getFullYear() - 8, today.getMonth(), today.getDate());
    const dobStr = dob.toISOString().split('T')[0];
    const { result } = renderHook(() => useAgeTheme(dobStr));
    expect(result.current).toBe('primaire');
  });

  it('returns "college" for age >= 10', () => {
    const today = new Date();
    const dob = new Date(today.getFullYear() - 12, today.getMonth(), today.getDate());
    const dobStr = dob.toISOString().split('T')[0];
    const { result } = renderHook(() => useAgeTheme(dobStr));
    expect(result.current).toBe('college');
  });

  it('sets data-age-tier attribute on html element', () => {
    const today = new Date();
    const dob = new Date(today.getFullYear() - 4, today.getMonth(), today.getDate());
    const dobStr = dob.toISOString().split('T')[0];
    renderHook(() => useAgeTheme(dobStr));
    expect(document.documentElement.getAttribute('data-age-tier')).toBe('maternelle');
  });

  it('returns "maternelle" for age exactly 5', () => {
    const today = new Date();
    const dob = new Date(today.getFullYear() - 5, today.getMonth(), today.getDate());
    const dobStr = dob.toISOString().split('T')[0];
    const { result } = renderHook(() => useAgeTheme(dobStr));
    expect(result.current).toBe('maternelle');
  });

  it('returns "college" for age exactly 10', () => {
    const today = new Date();
    const dob = new Date(today.getFullYear() - 10, today.getMonth(), today.getDate());
    const dobStr = dob.toISOString().split('T')[0];
    const { result } = renderHook(() => useAgeTheme(dobStr));
    expect(result.current).toBe('college');
  });

  it('updates tier when dateOfBirth changes', () => {
    const today = new Date();
    const youngDob = new Date(today.getFullYear() - 4, today.getMonth(), today.getDate())
      .toISOString()
      .split('T')[0];
    const oldDob = new Date(today.getFullYear() - 12, today.getMonth(), today.getDate())
      .toISOString()
      .split('T')[0];

    const { result, rerender } = renderHook(({ dob }: { dob: string }) => useAgeTheme(dob), {
      initialProps: { dob: youngDob },
    });
    expect(result.current).toBe('maternelle');

    rerender({ dob: oldDob });
    expect(result.current).toBe('college');
  });
});

// ---------------------------------------------------------------------------
// useFocusManagement
// ---------------------------------------------------------------------------

function routerWrapper({ children }: { children: ReactNode }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe('useFocusManagement', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('runs without crashing', () => {
    expect(() => {
      renderHook(() => useFocusManagement(), { wrapper: routerWrapper });
    }).not.toThrow();
  });

  it('calls requestAnimationFrame on mount', () => {
    const rafSpy = vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      cb(0);
      return 0;
    });
    renderHook(() => useFocusManagement(), { wrapper: routerWrapper });
    expect(rafSpy).toHaveBeenCalled();
  });

  it('focuses main h1 when present', () => {
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      cb(0);
      return 0;
    });
    // Create a main h1 in the document
    const main = document.createElement('main');
    const h1 = document.createElement('h1');
    h1.textContent = 'Test Page';
    main.appendChild(h1);
    document.body.appendChild(main);

    const focusSpy = vi.spyOn(h1, 'focus');
    renderHook(() => useFocusManagement(), { wrapper: routerWrapper });

    expect(focusSpy).toHaveBeenCalled();

    document.body.removeChild(main);
  });

  it('focuses #main-content when no h1', () => {
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      cb(0);
      return 0;
    });
    const mainContent = document.createElement('div');
    mainContent.id = 'main-content';
    document.body.appendChild(mainContent);

    const focusSpy = vi.spyOn(mainContent, 'focus');
    renderHook(() => useFocusManagement(), { wrapper: routerWrapper });

    expect(focusSpy).toHaveBeenCalled();

    document.body.removeChild(mainContent);
  });

  it('cancels animation frame on unmount', () => {
    const cancelSpy = vi.spyOn(window, 'cancelAnimationFrame');
    vi.spyOn(window, 'requestAnimationFrame').mockReturnValue(42);

    const { unmount } = renderHook(() => useFocusManagement(), { wrapper: routerWrapper });
    unmount();

    expect(cancelSpy).toHaveBeenCalledWith(42);
  });
});
