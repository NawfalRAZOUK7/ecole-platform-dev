import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useFeeStructures,
  useFeeAssignments,
  useCreateFeeStructure,
  useUpdateFeeStructure,
  useCreateFeeAssignment,
  useBulkFeeAssignments,
  useGenerateInvoices,
  useSiblingPolicy,
  useUpdateSiblingPolicy,
  useLateFeePolicy,
  useUpdateLateFeePolicy,
  usePaymentPlans,
  useCreatePaymentPlan,
  usePaymentPlan,
} from '@/features/billing/model/useBilling';

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

const mockFeeStructure = {
  id: 'fs-1',
  school_id: 'sch-1',
  academic_year_id: 'ay-1',
  name: 'Frais de scolarité',
  amount: 5000,
  currency: 'MAD',
  frequency: 'monthly',
  due_day: 5,
  applies_to_level: null,
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: null,
};

const mockFeeAssignment = {
  id: 'fa-1',
  fee_structure_id: 'fs-1',
  student_id: 'std-1',
  school_id: 'sch-1',
  discount_percent: null,
  discount_reason: null,
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
};

const mockPaymentPlan = {
  id: 'pp-1',
  student_id: 'std-1',
  student_name: 'Ahmed Alami',
  name: 'Plan mensuel',
  total_amount: 10000,
  start_date: '2026-09-01',
  status: 'active' as const,
  installments: [],
  created_at: '2026-01-01T00:00:00Z',
};

describe('useFeeStructures', () => {
  it('returns fee structures on success', async () => {
    server.use(
      http.get('/api/v1/billing/fee-structures', () => apiListResponse([mockFeeStructure])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFeeStructures(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockFeeStructure]);
  });

  it('accepts status filter', async () => {
    server.use(
      http.get('/api/v1/billing/fee-structures', () => apiListResponse([mockFeeStructure])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFeeStructures('active'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeDefined();
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/billing/fee-structures', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFeeStructures(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useFeeAssignments', () => {
  it('returns fee assignments on success', async () => {
    server.use(
      http.get('/api/v1/billing/fee-assignments', () => apiListResponse([mockFeeAssignment])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFeeAssignments(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockFeeAssignment]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/billing/fee-assignments', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFeeAssignments(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCreateFeeStructure', () => {
  it('posts successfully', async () => {
    server.use(
      http.post('/api/v1/billing/fee-structures', () => apiResponse(null)),
      http.get('/api/v1/billing/fee-structures', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateFeeStructure(), { wrapper });
    act(() => {
      result.current.mutate({
        name: 'Test',
        amount: 1000,
        currency: 'MAD',
        frequency: 'monthly',
        due_day: 5,
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles mutation error', async () => {
    server.use(http.post('/api/v1/billing/fee-structures', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateFeeStructure(), { wrapper });
    act(() => {
      result.current.mutate({
        name: 'Test',
        amount: 1000,
        currency: 'MAD',
        frequency: 'monthly',
        due_day: 5,
      });
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateFeeStructure', () => {
  it('updates successfully', async () => {
    server.use(
      http.put('/api/v1/billing/fee-structures/fs-1', () => apiResponse(null)),
      http.get('/api/v1/billing/fee-structures', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateFeeStructure(), { wrapper });
    act(() => {
      result.current.mutate({
        feeStructureId: 'fs-1',
        payload: {
          name: 'Updated',
          amount: 1500,
          currency: 'MAD',
          frequency: 'monthly',
          due_day: 10,
        },
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCreateFeeAssignment', () => {
  it('posts successfully', async () => {
    server.use(
      http.post('/api/v1/billing/fee-assignments', () => apiResponse(null)),
      http.get('/api/v1/billing/fee-assignments', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateFeeAssignment(), { wrapper });
    act(() => {
      result.current.mutate({ fee_structure_id: 'fs-1', student_id: 'std-1' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useBulkFeeAssignments', () => {
  it('returns result on success', async () => {
    const bulkResult = { created: 10, skipped: 2 };
    server.use(http.post('/api/v1/billing/fee-assignments/bulk', () => apiResponse(bulkResult)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBulkFeeAssignments(), { wrapper });
    act(() => {
      result.current.mutate({ fee_structure_id: 'fs-1', class_id: 'cls-1' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(bulkResult);
  });
});

describe('useGenerateInvoices', () => {
  it('generates invoices and returns result', async () => {
    const genResult = { generated: 25, skipped: 0, total_amount: 125000, currency: 'MAD' };
    server.use(http.post('/api/v1/billing/generate-invoices', () => apiResponse(genResult)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useGenerateInvoices(), { wrapper });
    act(() => {
      result.current.mutate({
        fee_structure_id: 'fs-1',
        issued_date: '2026-09-01',
        due_date: '2026-09-30',
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(genResult);
  });
});

describe('useSiblingPolicy', () => {
  it('returns sibling policy on success', async () => {
    const policy = {
      discounts: [{ sibling_rank: 2, discount_percent: 10 }],
      max_siblings_covered: 3,
    };
    server.use(http.get('/api/v1/billing/sibling-policy', () => apiResponse(policy)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSiblingPolicy(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(policy);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/billing/sibling-policy', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSiblingPolicy(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateSiblingPolicy', () => {
  it('updates sibling policy', async () => {
    const policy = {
      discounts: [{ sibling_rank: 2, discount_percent: 15 }],
      max_siblings_covered: 4,
    };
    server.use(
      http.put('/api/v1/billing/sibling-policy', () => apiResponse(policy)),
      http.get('/api/v1/billing/sibling-policy', () => apiResponse(policy)),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateSiblingPolicy(), { wrapper });
    act(() => {
      result.current.mutate({
        discounts: [{ sibling_rank: 2, discount_percent: 15 }],
        max_siblings_covered: 4,
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useLateFeePolicy', () => {
  it('returns late fee policy on success', async () => {
    const policy = { grace_period_days: 5, fee_percent: 2, max_fee_cap: 500 };
    server.use(http.get('/api/v1/billing/late-fee-policy', () => apiResponse(policy)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useLateFeePolicy(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(policy);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/billing/late-fee-policy', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useLateFeePolicy(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateLateFeePolicy', () => {
  it('updates late fee policy', async () => {
    const policy = { grace_period_days: 7, fee_percent: 3, max_fee_cap: 600 };
    server.use(
      http.put('/api/v1/billing/late-fee-policy', () => apiResponse(policy)),
      http.get('/api/v1/billing/late-fee-policy', () => apiResponse(policy)),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateLateFeePolicy(), { wrapper });
    act(() => {
      result.current.mutate({ grace_period_days: 7, fee_percent: 3, max_fee_cap: 600 });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('usePaymentPlans', () => {
  it('returns payment plans on success', async () => {
    server.use(http.get('/api/v1/billing/payment-plans', () => apiListResponse([mockPaymentPlan])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePaymentPlans(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockPaymentPlan]);
  });

  it('accepts filter params', async () => {
    server.use(http.get('/api/v1/billing/payment-plans', () => apiListResponse([mockPaymentPlan])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePaymentPlans({ student_id: 'std-1' }), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/billing/payment-plans', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePaymentPlans(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCreatePaymentPlan', () => {
  it('creates a payment plan', async () => {
    server.use(
      http.post('/api/v1/billing/payment-plans', () => apiResponse(mockPaymentPlan)),
      http.get('/api/v1/billing/payment-plans', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreatePaymentPlan(), { wrapper });
    act(() => {
      result.current.mutate({
        student_id: 'std-1',
        name: 'Plan mensuel',
        total_amount: 10000,
        start_date: '2026-09-01',
        installments: [{ due_date: '2026-09-30', amount: 5000 }],
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockPaymentPlan);
  });
});

describe('usePaymentPlan', () => {
  it('returns payment plan detail', async () => {
    server.use(http.get('/api/v1/billing/payment-plans/pp-1', () => apiResponse(mockPaymentPlan)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePaymentPlan('pp-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockPaymentPlan);
  });

  it('does not fetch when planId is empty', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePaymentPlan(''), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});
