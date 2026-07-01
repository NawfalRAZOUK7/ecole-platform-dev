import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import type { ApiError } from '@/core/api/client';

const mockApiError: ApiError = {
  code: 'ERR-SYS-500',
  message: 'Something went wrong',
  category: 'system',
  retryable: false,
  timestamp: '2026-01-01T00:00:00Z',
};

describe('useDismissibleError', () => {
  it('returns the error when not dismissed', () => {
    const { result } = renderHook(() => useDismissibleError(mockApiError));
    expect(result.current.error).toBe(mockApiError);
  });

  it('returns null when error is null', () => {
    const { result } = renderHook(() => useDismissibleError(null));
    expect(result.current.error).toBeNull();
  });

  it('returns null after dismiss is called', () => {
    const { result } = renderHook(() => useDismissibleError(mockApiError));
    expect(result.current.error).toBe(mockApiError);
    act(() => {
      result.current.dismiss();
    });
    expect(result.current.error).toBeNull();
  });

  it('provides a dismiss function', () => {
    const { result } = renderHook(() => useDismissibleError(mockApiError));
    expect(typeof result.current.dismiss).toBe('function');
  });

  it('resets dismissed state when error changes', () => {
    const newError: ApiError = {
      code: 'ERR-NEW',
      message: 'New error',
      category: 'system',
      retryable: false,
      timestamp: '2026-01-01T00:00:00Z',
    };

    const { result, rerender } = renderHook(
      ({ error }: { error: ApiError | null }) => useDismissibleError(error),
      { initialProps: { error: mockApiError } },
    );

    // Dismiss the first error
    act(() => {
      result.current.dismiss();
    });
    expect(result.current.error).toBeNull();

    // Change to a new error — should reset dismissed state
    rerender({ error: newError });
    expect(result.current.error).toBe(newError);
  });

  it('handles string errors', () => {
    const { result } = renderHook(() => useDismissibleError('A plain string error'));
    expect(result.current.error).toBe('A plain string error');
  });

  it('dismisses string errors', () => {
    const { result } = renderHook(() => useDismissibleError('An error message'));
    act(() => {
      result.current.dismiss();
    });
    expect(result.current.error).toBeNull();
  });

  it('resets when switching from null to error', () => {
    const { result, rerender } = renderHook(
      ({ error }: { error: ApiError | null }) => useDismissibleError(error),
      { initialProps: { error: null } },
    );
    expect(result.current.error).toBeNull();

    rerender({ error: mockApiError });
    expect(result.current.error).toBe(mockApiError);
  });

  it('remains null when error stays null', () => {
    const { result, rerender } = renderHook(
      ({ error }: { error: null }) => useDismissibleError(error),
      { initialProps: { error: null } },
    );
    rerender({ error: null });
    expect(result.current.error).toBeNull();
  });
});
