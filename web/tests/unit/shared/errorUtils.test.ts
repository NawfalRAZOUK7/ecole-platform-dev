import { describe, it, expect } from 'vitest';
import { toBannerError } from '@/shared/ui/errorUtils';
import { ApiClientError, type ApiError } from '@/core/api/client';

const mockApiError: ApiError = {
  code: 'ERR-SYS-500',
  message: 'Internal server error',
  category: 'system',
  retryable: false,
  timestamp: '2026-01-01T00:00:00Z',
};

describe('toBannerError', () => {
  it('returns null when error is null', () => {
    expect(toBannerError(null, 'Fallback')).toBeNull();
  });

  it('returns null when error is undefined', () => {
    expect(toBannerError(undefined, 'Fallback')).toBeNull();
  });

  it('returns null when error is falsy empty string', () => {
    expect(toBannerError('', 'Fallback')).toBeNull();
  });

  it('returns null when error is 0 (falsy)', () => {
    expect(toBannerError(0, 'Fallback')).toBeNull();
  });

  it('extracts apiError from ApiClientError', () => {
    const error = new ApiClientError(500, mockApiError);
    const result = toBannerError(error, 'Fallback');
    expect(result).toBe(mockApiError);
    expect(typeof result).toBe('object');
    if (result && typeof result === 'object' && 'code' in result) {
      expect(result.code).toBe('ERR-SYS-500');
      expect(result.message).toBe('Internal server error');
    }
  });

  it('returns error message from standard Error', () => {
    const error = new Error('Something broke');
    const result = toBannerError(error, 'Fallback');
    expect(result).toBe('Something broke');
  });

  it('returns fallback for unknown error type (object)', () => {
    const result = toBannerError({ weird: true }, 'Fallback message');
    expect(result).toBe('Fallback message');
  });

  it('returns fallback for unknown error type (number)', () => {
    const result = toBannerError(42, 'Fallback');
    expect(result).toBe('Fallback');
  });

  it('returns a non-empty string error as the message', () => {
    const result = toBannerError(new Error('Network timeout'), 'Fallback');
    expect(result).toBe('Network timeout');
  });

  it('preserves all apiError fields from ApiClientError', () => {
    const detailedApiError: ApiError = {
      code: 'ERR-AUTH-001',
      message: 'Authentication required',
      category: 'authn',
      retryable: false,
      timestamp: '2026-06-01T00:00:00Z',
      correlation_id: 'abc-123',
      details: { extra: 'info' },
    };
    const error = new ApiClientError(401, detailedApiError);
    const result = toBannerError(error, 'Fallback');
    expect(result).toBe(detailedApiError);
    if (result && typeof result === 'object' && 'correlation_id' in result) {
      expect(result.correlation_id).toBe('abc-123');
    }
  });

  it('handles ApiClientError with 404 status', () => {
    const notFoundError: ApiError = {
      code: 'ERR-404',
      message: 'Not found',
      category: 'not_found',
      retryable: false,
      timestamp: '2026-01-01T00:00:00Z',
    };
    const error = new ApiClientError(404, notFoundError);
    const result = toBannerError(error, 'Resource not found');
    expect(result).toBe(notFoundError);
  });
});
