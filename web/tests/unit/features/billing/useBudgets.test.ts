import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useBudgets,
  useBudgetDetail,
  useBudgetAllocations,
  useBudgetAllocation,
  useBudgetAnalytics,
  useCreateBudget,
  useDeleteBudget,
  useCreateAllocation,
  useUpdateAllocation,
  useApproveBudgetRequest,
  useRejectBudgetRequest,
  useBudgetRequestDetail,
  useAllocationTransactions,
  useCreateTransaction,
} from '@/features/billing/budgets/model/useBudgets';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) =>
    QueryClientProvider({ client: queryClient, children });
}

function apiListResponse<T>(data: T[]) {
  return HttpResponse.json({
    data,
    meta: {
      next_cursor: null,
      has_more: false,
      timestamp: new Date().toISOString(),
      version: 'test',
    },
  });
}

function apiResponse<T>(data: T) {
  return HttpResponse.json({
    data,
    meta: { timestamp: new Date().toISOString(), version: 'test' },
  });
}

function apiError(status = 500) {
  return HttpResponse.json(
    {
      error: { code: 'ERR', message: 'fail', category: 'system', retryable: false, timestamp: '' },
    },
    { status },
  );
}

const mockBudget = {
  id: 'bud-1',
  name: 'Operations',
  total_amount: 120000,
  spent_amount: 40000,
  remaining_amount: 80000,
  status: 'active',
  currency: 'MAD',
  start_date: '2026-01-01',
  end_date: '2026-12-31',
  created_at: '2026-01-05T08:00:00Z',
};

const mockAllocation = {
  id: 'alloc-1',
  budget_id: 'bud-1',
  name: 'Materials',
  allocated_amount: 20000,
  spent_amount: 5000,
  remaining_amount: 15000,
  currency: 'MAD',
  status: 'active',
  created_at: '2026-01-05T08:00:00Z',
};

const mockAnalytics = {
  total_budgets: 5,
  total_allocated: 500000,
  total_spent: 200000,
  utilization_rate: 40,
};

const mockTransaction = {
  id: 'txn-1',
  allocation_id: 'alloc-1',
  amount: 1000,
  currency: 'MAD',
  description: 'Test purchase',
  created_at: '2026-01-10T10:00:00Z',
};

describe('useBudgets', () => {
  it('returns budgets on success', async () => {
    server.use(http.get('/api/v1/budgets', () => apiListResponse([mockBudget])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgets(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockBudget]);
  });

  it('accepts filters', async () => {
    server.use(http.get('/api/v1/budgets', () => apiListResponse([mockBudget])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgets({ status: 'active' }), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/budgets', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgets(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useBudgetDetail', () => {
  it('returns budget detail on success', async () => {
    server.use(http.get('/api/v1/budgets/bud-1', () => apiResponse(mockBudget)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetDetail('bud-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockBudget);
  });

  it('does not fetch when id is empty', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetDetail(''), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useBudgetAllocations', () => {
  it('returns allocations on success', async () => {
    server.use(http.get('/api/v1/budgets/bud-1/allocations', () => apiResponse([mockAllocation])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetAllocations('bud-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockAllocation]);
  });

  it('does not fetch when id is empty', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetAllocations(''), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useBudgetAllocation', () => {
  it('returns allocation detail on success', async () => {
    server.use(http.get('/api/v1/budgets/allocations/alloc-1', () => apiResponse(mockAllocation)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetAllocation('alloc-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockAllocation);
  });
});

describe('useBudgetAnalytics', () => {
  it('returns analytics on success', async () => {
    server.use(http.get('/api/v1/budgets/analytics', () => apiResponse(mockAnalytics)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetAnalytics(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockAnalytics);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/budgets/analytics', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetAnalytics(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCreateBudget', () => {
  it('creates a budget', async () => {
    server.use(http.post('/api/v1/budgets', () => apiResponse(mockBudget)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateBudget(), { wrapper });
    act(() => {
      result.current.mutate({
        name: 'New Budget',
        total_amount: 50000,
        currency: 'MAD',
        start_date: '2026-01-01',
        end_date: '2026-12-31',
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles mutation error', async () => {
    server.use(http.post('/api/v1/budgets', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateBudget(), { wrapper });
    act(() => {
      result.current.mutate({
        name: 'Test',
        total_amount: 1000,
        currency: 'MAD',
        start_date: '2026-01-01',
        end_date: '2026-12-31',
      });
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useDeleteBudget', () => {
  it('deletes a budget', async () => {
    server.use(http.delete('/api/v1/budgets/bud-1', () => apiResponse(null)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDeleteBudget(), { wrapper });
    act(() => {
      result.current.mutate('bud-1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCreateAllocation', () => {
  it('creates an allocation', async () => {
    server.use(http.post('/api/v1/budgets/bud-1/allocations', () => apiResponse(mockAllocation)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateAllocation(), { wrapper });
    act(() => {
      result.current.mutate({
        budgetId: 'bud-1',
        payload: { name: 'Materials', allocated_amount: 20000, currency: 'MAD' },
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useUpdateAllocation', () => {
  it('updates an allocation', async () => {
    server.use(http.put('/api/v1/budgets/allocations/alloc-1', () => apiResponse(mockAllocation)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateAllocation(), { wrapper });
    act(() => {
      result.current.mutate({
        allocationId: 'alloc-1',
        payload: { allocated_amount: 25000 },
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useApproveBudgetRequest', () => {
  it('approves a request', async () => {
    server.use(
      http.post('/api/v1/budgets/requests/req-1/approve', () =>
        apiResponse({ id: 'req-1', status: 'approved' }),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApproveBudgetRequest(), { wrapper });
    act(() => {
      result.current.mutate({ requestId: 'req-1', reviewComment: 'Approved' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useRejectBudgetRequest', () => {
  it('rejects a request', async () => {
    server.use(
      http.post('/api/v1/budgets/requests/req-1/reject', () =>
        apiResponse({ id: 'req-1', status: 'rejected' }),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useRejectBudgetRequest(), { wrapper });
    act(() => {
      result.current.mutate({ requestId: 'req-1', reviewComment: 'Not justified' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useBudgetRequestDetail', () => {
  it('returns request detail', async () => {
    const mockRequest = { id: 'req-1', allocation_id: 'alloc-1', amount: 500, status: 'pending' };
    server.use(http.get('/api/v1/budgets/requests/req-1', () => apiResponse(mockRequest)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetRequestDetail('req-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockRequest);
  });

  it('does not fetch when requestId is empty', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBudgetRequestDetail(''), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useAllocationTransactions', () => {
  it('returns transactions for an allocation', async () => {
    server.use(
      http.get('/api/v1/budgets/allocations/alloc-1/transactions', () =>
        apiListResponse([mockTransaction]),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAllocationTransactions('alloc-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockTransaction]);
  });

  it('does not fetch when allocationId is empty', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAllocationTransactions(''), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateTransaction', () => {
  it('creates a transaction', async () => {
    server.use(
      http.post('/api/v1/budgets/allocations/alloc-1/transactions', () =>
        apiResponse(mockTransaction),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateTransaction(), { wrapper });
    act(() => {
      result.current.mutate({
        allocationId: 'alloc-1',
        payload: { amount: 1000, description: 'Purchase', transaction_date: '2026-01-10' },
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockTransaction);
  });
});
