import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { authService } from '@/features/auth/api/auth.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };

describe('authService', () => {
  const loginResponse = {
    access_token: 'tok-abc',
    token_type: 'bearer',
    expires_in: 3600,
    user_id: 'user-1',
    school_id: 'school-1',
    role: 'teacher',
  };

  it('register posts registration', async () => {
    server.use(
      http.post('/api/v1/auth/register', () =>
        HttpResponse.json({ data: { ...loginResponse, email_verification_required: true }, meta }),
      ),
    );
    const result = await authService.register({
      code: 'invite-code',
      email: 'test@school.ma',
      full_name: 'Test User',
      phone: null,
      password: 'password123',
      profile_data: {},
    });
    expect(result.data.access_token).toBe('tok-abc');
  });

  it('verifyEmail posts email verification', async () => {
    server.use(
      http.post('/api/v1/auth/verify-email', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await authService.verifyEmail({
      user_id: 'user-1',
      school_id: 'school-1',
      otp: '123456',
    });
    expect(result).toBeDefined();
  });

  it('login posts credentials and returns token', async () => {
    server.use(
      http.post('/api/v1/auth/login', () => HttpResponse.json({ data: loginResponse, meta })),
    );
    const result = await authService.login({
      email: 'test@school.ma',
      password: 'pass',
      school_id: 'school-1',
    });
    expect(result.data.role).toBe('teacher');
  });

  it('refresh posts token refresh', async () => {
    server.use(
      http.post('/api/v1/auth/refresh', () =>
        HttpResponse.json({ data: { access_token: 'new-tok', expires_in: 3600 }, meta }),
      ),
    );
    const result = await authService.refresh();
    expect(result.data.access_token).toBe('new-tok');
  });

  it('logout posts logout', async () => {
    server.use(
      http.post('/api/v1/auth/logout', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await authService.logout();
    expect(result).toBeDefined();
  });

  it('getMe returns user info', async () => {
    server.use(
      http.get('/api/v1/auth/me', () =>
        HttpResponse.json({
          data: {
            user_id: 'user-1',
            email: 'test@school.ma',
            full_name: 'Test User',
            role: 'teacher',
            school_id: 'school-1',
          },
          meta,
        }),
      ),
    );
    const result = await authService.getMe();
    expect(result.data.user_id).toBe('user-1');
  });

  it('getLoginHistory returns login history', async () => {
    server.use(http.get('/api/v1/auth/login-history', () => HttpResponse.json({ data: [], meta })));
    const result = await authService.getLoginHistory();
    expect(result.data).toEqual([]);
  });

  it('consumeInvite posts invite consumption', async () => {
    server.use(
      http.post('/api/v1/invites/consume', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await authService.consumeInvite('invite-code');
    expect(result).toBeDefined();
  });

  it('requestRecovery posts recovery request', async () => {
    server.use(
      http.post('/api/v1/recovery/request', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await authService.requestRecovery('test@school.ma');
    expect(result).toBeDefined();
  });

  it('verifyRecovery posts recovery verification', async () => {
    server.use(
      http.post('/api/v1/recovery/verify', () =>
        HttpResponse.json({ data: { valid: true }, meta }),
      ),
    );
    const result = await authService.verifyRecovery('token-abc', '123456');
    expect(result.data.valid).toBe(true);
  });

  it('resetPassword posts password reset', async () => {
    server.use(
      http.post('/api/v1/recovery/reset', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await authService.resetPassword('token-abc', 'newpassword123');
    expect(result).toBeDefined();
  });

  it('verify2fa posts 2FA verification', async () => {
    server.use(
      http.post('/api/v1/auth/2fa/verify', () => HttpResponse.json({ data: loginResponse, meta })),
    );
    const result = await authService.verify2fa({ code: '123456' });
    expect(result.data.user_id).toBe('user-1');
  });
});
