/**
 * Tests for src/shared/hooks/useDismissibleError.ts
 * Covers:
 *  - reset on error change
 *  - dismiss() hides the error
 *  - re-dismiss after a new error
 */
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useDismissibleError } from '@/shared/hooks/useDismissibleError';

describe('shared/hooks/useDismissibleError', () => {
  it('returns the input error verbatim when not dismissed', () => {
    const { result } = renderHook(() => useDismissibleError('Boom'));
    expect(result.current.error).toBe('Boom');
  });

  it('hides the error after dismiss() is called', () => {
    const { result } = renderHook(() => useDismissibleError('Boom'));
    expect(result.current.error).toBe('Boom');

    act(() => {
      result.current.dismiss();
    });

    expect(result.current.error).toBeNull();
  });

  it('un-dismisses when the error reference changes', () => {
    const { result, rerender } = renderHook(
      ({ err }: { err: string | null }) => useDismissibleError(err),
      {
        initialProps: { err: 'first' },
      },
    );

    act(() => {
      result.current.dismiss();
    });
    expect(result.current.error).toBeNull();

    rerender({ err: 'second' });
    expect(result.current.error).toBe('second');
  });

  it('handles a null initial error gracefully', () => {
    const { result } = renderHook(() => useDismissibleError(null));
    expect(result.current.error).toBeNull();
  });

  it('handles an ApiError-shaped object', () => {
    // The hook is generic over string | ApiError | null — pass any object.
    const apiError = { message: 'forbidden', code: 'ERR-403', details: null };
    const { result } = renderHook(() => useDismissibleError(apiError as never));
    expect(result.current.error).toEqual(apiError);

    act(() => {
      result.current.dismiss();
    });
    expect(result.current.error).toBeNull();
  });
});
