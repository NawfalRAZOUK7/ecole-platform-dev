import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import {
  adminQueryKeys,
  useActivateAdminUser,
  useAdminAnalytics,
  useAdminAuditLogs,
  useAdminBatchRegister,
  useAdminDashboard,
  useAdminInvitations,
  useAdminJustifications,
  useAdminParentChildLinks,
  useAdminUserSearch,
  useAdminUsers,
  useChangeAdminUserRole,
  useCreateInvitation,
  useCreateParentChildLink,
  useCreateSchool,
  useDeleteSchool,
  useImpersonateUser,
  useListSchools,
  useRevokeInvitation,
  useRevokeParentChildLink,
  useReviewJustification,
  useStopImpersonation,
  useSuspendAdminUser,
  useUserLoginHistory,
} from '@/features/admin/model/useAdmin';
import { apiErrorResponse, apiListResponse, apiResponse, server } from '../../../utils/mocks';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) =>
    QueryClientProvider({ client: queryClient, children });
}

describe('adminQueryKeys', () => {
  it('all returns ["admin"]', () => {
    expect(adminQueryKeys.all).toEqual(['admin']);
  });

  it('dashboard returns ["admin", "dashboard"]', () => {
    expect(adminQueryKeys.dashboard()).toEqual(['admin', 'dashboard']);
  });

  it('analytics returns ["admin", "analytics", period]', () => {
    expect(adminQueryKeys.analytics(30)).toEqual(['admin', 'analytics', 30]);
  });

  it('users returns ["admin", "users", filters]', () => {
    const filters = { role: 'STD' };
    expect(adminQueryKeys.users(filters)).toEqual(['admin', 'users', filters]);
  });

  it('userSearch returns correct key', () => {
    expect(adminQueryKeys.userSearch('john', 'STD')).toEqual([
      'admin',
      'user-search',
      'STD',
      'john',
    ]);
  });

  it('invitations returns correct key', () => {
    const filters = {};
    expect(adminQueryKeys.invitations(filters)).toEqual(['admin', 'invitations', filters]);
  });

  it('justifications returns correct key', () => {
    const filters = {};
    expect(adminQueryKeys.justifications(filters)).toEqual(['admin', 'justifications', filters]);
  });

  it('parentChildLinks returns correct key', () => {
    const filters = {};
    expect(adminQueryKeys.parentChildLinks(filters)).toEqual([
      'admin',
      'parent-child-links',
      filters,
    ]);
  });

  it('auditLogs returns correct key', () => {
    const filters = {};
    expect(adminQueryKeys.auditLogs(filters)).toEqual(['admin', 'audit', filters]);
  });
});

describe('useAdminDashboard', () => {
  it('fetches dashboard data successfully', async () => {
    const mockData = {
      users: 100,
      active_sessions: 5,
      active_invitations: 2,
      audit_events_24h: 10,
      pending_justifications: 1,
      users_by_role: { ADM: 1, TCH: 9, STD: 90 },
    };
    server.use(http.get('/api/v1/admin/dashboard', () => apiResponse(mockData)));

    const { result } = renderHook(() => useAdminDashboard(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.users).toBe(100);
  });

  it('handles error state', async () => {
    server.use(http.get('/api/v1/admin/dashboard', () => apiErrorResponse('Dashboard error')));
    const { result } = renderHook(() => useAdminDashboard(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useAdminAnalytics', () => {
  it('fetches analytics with period', async () => {
    const kpiItem = {
      kpi_id: 'dau',
      name: 'Daily Active Users',
      value: 50,
      unit: 'users',
      period: '7d',
    };
    const mockKpis = {
      kpis: [kpiItem],
      period: '7d',
      computed_at: new Date().toISOString(),
    };
    server.use(http.get('/api/v1/kpis', () => apiResponse(mockKpis)));

    const { result } = renderHook(() => useAdminAnalytics(7), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.history).toEqual(expect.any(Array));
  });

  it('history starts empty', () => {
    server.use(
      http.get('/api/v1/kpis', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiResponse({ kpis: [], period: '7d', computed_at: new Date().toISOString() });
      }),
    );
    const { result } = renderHook(() => useAdminAnalytics(7), { wrapper: createWrapper() });
    expect(result.current.history).toEqual([]);
  });
});

describe('useAdminAuditLogs', () => {
  it('fetches audit logs in infinite query', async () => {
    const mockLogs = [
      {
        id: 'log-1',
        action_type: 'LOGIN',
        outcome: 'success',
        actor_id: 'u1',
        target_type: null,
        target_id: null,
        error_code: null,
        correlation_id: null,
        ip_address: null,
        created_at: null,
      },
    ];
    server.use(http.get('/api/v1/admin/audit-logs', () => apiListResponse(mockLogs)));

    const { result } = renderHook(() => useAdminAuditLogs({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0]?.data).toHaveLength(1);
  });
});

describe('useAdminUsers', () => {
  it('fetches users list', async () => {
    const mockUsers = [
      {
        id: 'u1',
        email: 'a@b.com',
        full_name: 'Test User',
        status: 'active',
        role: 'STD',
        created_at: null,
        email_verified: true,
        totp_enabled: false,
      },
    ];
    server.use(http.get('/api/v1/admin/users', () => apiListResponse(mockUsers)));

    const { result } = renderHook(() => useAdminUsers({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0]?.data).toHaveLength(1);
  });
});

describe('useAdminUserSearch', () => {
  it('is disabled when search is less than 2 characters', () => {
    const { result } = renderHook(() => useAdminUserSearch('a', 'STD'), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('is enabled when search is 2+ characters', async () => {
    const mockUsers = [
      {
        id: 'u1',
        email: 'alice@school.com',
        full_name: 'Alice',
        status: 'active',
        role: 'STD',
        created_at: null,
        email_verified: true,
        totp_enabled: false,
      },
    ];
    server.use(http.get('/api/v1/admin/users', () => apiListResponse(mockUsers)));

    const { result } = renderHook(() => useAdminUserSearch('ali', 'STD'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useSuspendAdminUser', () => {
  it('calls suspend endpoint and returns userId', async () => {
    server.use(http.put('/api/v1/admin/users/:userId/suspend', () => apiResponse({})));

    const { result } = renderHook(() => useSuspendAdminUser(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate('user-123');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useActivateAdminUser', () => {
  it('calls activate endpoint and returns userId', async () => {
    server.use(http.put('/api/v1/admin/users/:userId/activate', () => apiResponse({})));

    const { result } = renderHook(() => useActivateAdminUser(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate('user-123');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useChangeAdminUserRole', () => {
  it('calls change-role endpoint', async () => {
    server.use(http.put('/api/v1/admin/users/:userId/role', () => apiResponse({})));

    const { result } = renderHook(() => useChangeAdminUserRole(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate({ userId: 'user-123', role: 'TCH' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useAdminBatchRegister', () => {
  it('calls batch-register endpoint', async () => {
    const mockResult = {
      created: [],
      errors: [],
      total_created: 0,
      total_errors: 0,
    };
    server.use(http.post('/api/v1/admin/register-batch', () => apiResponse(mockResult)));

    const { result } = renderHook(() => useAdminBatchRegister(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate([{ email: 'test@test.com', full_name: 'Test', role: 'STD' }]);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useAdminInvitations', () => {
  it('fetches invitations list', async () => {
    const mockInvite = {
      id: 'inv-1',
      role_target: 'STD',
      consumed_at: null,
      consumed_by: null,
      expires_at: new Date().toISOString(),
      created_at: null,
      issuer_user_id: null,
      status: 'pending',
    };
    server.use(http.get('/api/v1/admin/invitations', () => apiListResponse([mockInvite])));

    const { result } = renderHook(() => useAdminInvitations({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0]?.data).toHaveLength(1);
  });
});

describe('useCreateInvitation', () => {
  it('creates an invitation', async () => {
    const mockInvite = { code: 'INV-CODE-123' };
    server.use(http.post('/api/v1/invites/create', () => apiResponse(mockInvite)));

    const { result } = renderHook(() => useCreateInvitation(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate({ role_target: 'STD', expires_in_hours: 24 });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useRevokeInvitation', () => {
  it('revokes an invitation', async () => {
    server.use(http.post('/api/v1/invites/revoke', () => apiResponse({})));

    const { result } = renderHook(() => useRevokeInvitation(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate('inv-1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useAdminJustifications', () => {
  it('fetches justifications list', async () => {
    server.use(http.get('/api/v1/admin/justifications', () => apiListResponse([])));

    const { result } = renderHook(() => useAdminJustifications({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0]?.data).toEqual([]);
  });
});

describe('useReviewJustification', () => {
  it('reviews justification and returns result', async () => {
    server.use(http.post('/api/v1/attendance/justifications/:id/review', () => apiResponse({})));

    const { result } = renderHook(() => useReviewJustification(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate({ justificationId: 'j-1', decision: 'justified' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useAdminParentChildLinks', () => {
  it('fetches parent-child links', async () => {
    server.use(http.get('/api/v1/admin/parent-child-links', () => apiListResponse([])));

    const { result } = renderHook(() => useAdminParentChildLinks({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0]?.data).toEqual([]);
  });
});

describe('useCreateParentChildLink', () => {
  it('creates a parent-child link', async () => {
    // API uses query params: /admin/parent-child-links?parent_user_id=...&child_user_id=...
    server.use(http.post('/api/v1/admin/parent-child-links', () => apiResponse({})));

    const { result } = renderHook(() => useCreateParentChildLink(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate({ parentUserId: 'p-1', childUserId: 'c-1' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useRevokeParentChildLink', () => {
  it('revokes a parent-child link', async () => {
    server.use(http.delete('/api/v1/admin/parent-child-links/:linkId', () => apiResponse({})));

    const { result } = renderHook(() => useRevokeParentChildLink(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate('link-1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useImpersonateUser', () => {
  it('calls impersonate endpoint', async () => {
    const mockSession = { access_token: 'tok', user_id: 'u1', role: 'ADM' };
    server.use(http.post('/api/v1/admin/impersonate/:userId', () => apiResponse(mockSession)));

    const { result } = renderHook(() => useImpersonateUser(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate('user-1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useStopImpersonation', () => {
  it('calls stop-impersonation endpoint', async () => {
    server.use(http.post('/api/v1/admin/stop-impersonation', () => apiResponse({})));

    const { result } = renderHook(() => useStopImpersonation(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate();
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useUserLoginHistory', () => {
  it('fetches login history for user', async () => {
    const mockHistory = { events: [], total: 0 };
    server.use(
      http.get('/api/v1/admin/users/:userId/login-history', () => apiResponse(mockHistory)),
    );

    const { result } = renderHook(() => useUserLoginHistory('user-1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('is disabled when userId is empty', () => {
    const { result } = renderHook(() => useUserLoginHistory(''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateSchool', () => {
  it('calls create school endpoint', async () => {
    const mockSchool = {
      id: 's-1',
      name: 'École Test',
      code: 'ETT',
      address: null,
      city: null,
      phone: null,
      email: null,
      timezone: 'UTC',
      default_language: 'fr',
    };
    // adminService.createSchool calls /schools (not /admin/schools)
    server.use(http.post('/api/v1/schools', () => apiResponse(mockSchool)));

    const { result } = renderHook(() => useCreateSchool(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate({
        name: 'École Test',
        code: 'ETT',
        timezone: 'UTC',
        default_language: 'fr',
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useListSchools', () => {
  it('lists schools successfully', async () => {
    const mockSchool = {
      id: 's-1',
      name: 'École Test',
      code: 'ETT',
      address: null,
      city: null,
      phone: null,
      email: null,
      timezone: 'UTC',
      default_language: 'fr',
    };
    // adminService.listSchools calls /schools (list variant)
    server.use(http.get('/api/v1/schools', () => apiListResponse([mockSchool])));

    const { result } = renderHook(() => useListSchools(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(Array.isArray(result.current.data)).toBe(true);
  });
});

describe('useDeleteSchool', () => {
  it('calls delete school endpoint', async () => {
    server.use(http.delete('/api/v1/schools/:schoolId', () => apiResponse({})));

    const { result } = renderHook(() => useDeleteSchool(), { wrapper: createWrapper() });
    void act(() => {
      void result.current.mutate('school-1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
