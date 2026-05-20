import { ApiClientError, type ApiError } from '@/core/api/client';

export function toBannerError(error: unknown, fallback: string): ApiError | string | null {
  if (!error) {
    return null;
  }
  if (error instanceof ApiClientError) {
    return error.apiError;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}
