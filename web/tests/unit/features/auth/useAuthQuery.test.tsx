/**
 * Tests for src/features/auth/model/useAuthQuery.ts
 * Covers: useRegister, useVerifyEmail, useConsumeInvite
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import { server } from '../../../utils/mocks';
import { useRegister, useVerifyEmail, useConsumeInvite } from '@/features/auth/model/useAuthQuery';

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('useRegister', () => {
  it('starts in idle state', () => {
    const { result } = renderHook(() => useRegister(), { wrapper });
    expect(result.current.status).toBe('idle');
  });

  it('registers successfully', async () => {
    server.use(
      http.post('/api/v1/auth/register', () =>
        HttpResponse.json({
          data: {
            user_id: 'u1',
            school_id: 's1',
            role: 'STD',
            access_token: 'tok',
            email_verification_required: false,
          },
          meta: { timestamp: '', version: '' },
        }),
      ),
    );
    const { result } = renderHook(() => useRegister(), { wrapper });
    act(() => {
      result.current.mutate({
        invite_code: 'ABCD1234',
        full_name: 'Test User',
        email: 'test@test.com',
        password: 'SecurePass1!',
        class_level: null,
        date_of_birth: null,
        qualification: null,
        relationship_type: null,
        subject_specialty: null,
        phone: null,
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.user_id).toBe('u1');
  });

  it('handles registration error', async () => {
    server.use(
      http.post('/api/v1/auth/register', () =>
        HttpResponse.json(
          {
            error: {
              code: 'ERR',
              message: 'Invalid invite code',
              category: 'validation',
              retryable: false,
              timestamp: '',
            },
          },
          { status: 400 },
        ),
      ),
    );
    const { result } = renderHook(() => useRegister(), { wrapper });
    act(() => {
      result.current.mutate({
        invite_code: 'BADCODE',
        full_name: 'User',
        email: 'u@t.com',
        password: 'pass',
        class_level: null,
        date_of_birth: null,
        qualification: null,
        relationship_type: null,
        subject_specialty: null,
        phone: null,
      });
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useVerifyEmail', () => {
  it('starts idle', () => {
    const { result } = renderHook(() => useVerifyEmail(), { wrapper });
    expect(result.current.status).toBe('idle');
  });

  it('verifies email successfully', async () => {
    server.use(
      http.post('/api/v1/auth/verify-email', () =>
        HttpResponse.json({ data: null, meta: { timestamp: '', version: '' } }),
      ),
    );
    const { result } = renderHook(() => useVerifyEmail(), { wrapper });
    act(() => {
      result.current.mutate({ token: 'tok123', code: '123456' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useConsumeInvite', () => {
  it('starts idle', () => {
    const { result } = renderHook(() => useConsumeInvite(), { wrapper });
    expect(result.current.status).toBe('idle');
  });

  it('consumes invite code successfully', async () => {
    server.use(
      http.post('/api/v1/invites/consume', () =>
        HttpResponse.json({
          data: { school_id: 's1', school_name: 'Test School', role: 'STD' },
          meta: { timestamp: '', version: '' },
        }),
      ),
    );
    const { result } = renderHook(() => useConsumeInvite(), { wrapper });
    act(() => {
      result.current.mutate('ABCD1234');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles invalid invite code', async () => {
    server.use(
      http.post('/api/v1/invites/consume', () =>
        HttpResponse.json(
          {
            error: {
              code: 'ERR',
              message: 'Invalid code',
              category: 'validation',
              retryable: false,
              timestamp: '',
            },
          },
          { status: 400 },
        ),
      ),
    );
    const { result } = renderHook(() => useConsumeInvite(), { wrapper });
    act(() => {
      result.current.mutate('BADCODE');
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
