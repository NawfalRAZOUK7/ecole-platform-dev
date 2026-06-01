import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { billingService } from '@/features/billing/api/billing.api';
import { budgetsService } from '@/features/billing/budgets/api/budgets.api';
import { invoicesService } from '@/features/billing/invoices/api/invoices.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

// ── billingService ────────────────────────────────────────────────────────────

describe('billingService', () => {
  const feeStructure = {
    id: 'fee-1',
    school_id: 'school-1',
    academic_year_id: 'year-1',
    name: 'Tuition',
    amount: 5000,
    currency: 'MAD',
    frequency: 'monthly',
    due_day: 5,
    applies_to_level: null,
    status: 'active',
    created_at: new Date().toISOString(),
    updated_at: null,
  };

  it('listFeeStructures returns fee structures', async () => {
    server.use(
      http.get('/api/v1/billing/fee-structures', () =>
        HttpResponse.json({ data: [feeStructure], meta: listMeta }),
      ),
    );
    const result = await billingService.listFeeStructures();
    expect(result.data).toHaveLength(1);
    expect(result.data[0].name).toBe('Tuition');
  });

  it('createFeeStructure posts fee structure', async () => {
    server.use(
      http.post('/api/v1/billing/fee-structures', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await billingService.createFeeStructure({
      name: 'Tuition',
      amount: 5000,
      currency: 'MAD',
      frequency: 'monthly',
      due_day: 5,
    });
    expect(result).toBeDefined();
  });

  it('updateFeeStructure puts fee structure', async () => {
    server.use(
      http.put('/api/v1/billing/fee-structures/fee-1', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await billingService.updateFeeStructure('fee-1', {
      name: 'Updated Tuition',
      amount: 5500,
      currency: 'MAD',
      frequency: 'monthly',
      due_day: 5,
    });
    expect(result).toBeDefined();
  });

  it('listFeeAssignments returns assignments', async () => {
    server.use(
      http.get('/api/v1/billing/fee-assignments', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await billingService.listFeeAssignments();
    expect(result.data).toEqual([]);
  });

  it('createFeeAssignment posts assignment', async () => {
    server.use(
      http.post('/api/v1/billing/fee-assignments', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await billingService.createFeeAssignment({
      fee_structure_id: 'fee-1',
      student_id: 'student-1',
    });
    expect(result).toBeDefined();
  });

  it('createBulkFeeAssignments posts bulk', async () => {
    server.use(
      http.post('/api/v1/billing/fee-assignments/bulk', () =>
        HttpResponse.json({ data: { created: 5, skipped: 0 }, meta }),
      ),
    );
    const result = await billingService.createBulkFeeAssignments({
      fee_structure_id: 'fee-1',
      class_id: 'class-1',
    });
    expect(result.data.created).toBe(5);
  });

  it('generateInvoices posts invoice generation', async () => {
    server.use(
      http.post('/api/v1/billing/generate-invoices', () =>
        HttpResponse.json({
          data: { generated: 20, skipped: 0, total_amount: 100000, currency: 'MAD' },
          meta,
        }),
      ),
    );
    const result = await billingService.generateInvoices({
      fee_structure_id: 'fee-1',
      issued_date: '2025-01-01',
      due_date: '2025-01-31',
    });
    expect(result.data.generated).toBe(20);
  });

  it('getSiblingPolicy returns sibling policy', async () => {
    server.use(
      http.get('/api/v1/billing/sibling-policy', () =>
        HttpResponse.json({ data: { discounts: [], max_siblings_covered: 3 }, meta }),
      ),
    );
    const result = await billingService.getSiblingPolicy();
    expect(result.data.max_siblings_covered).toBe(3);
  });

  it('updateSiblingPolicy puts sibling policy', async () => {
    server.use(
      http.put('/api/v1/billing/sibling-policy', () =>
        HttpResponse.json({ data: { discounts: [], max_siblings_covered: 4 }, meta }),
      ),
    );
    const result = await billingService.updateSiblingPolicy({
      discounts: [],
      max_siblings_covered: 4,
    });
    expect(result.data.max_siblings_covered).toBe(4);
  });

  it('getLateFeePolicy returns late fee policy', async () => {
    server.use(
      http.get('/api/v1/billing/late-fee-policy', () =>
        HttpResponse.json({
          data: { grace_period_days: 5, fee_percent: 2, max_fee_cap: 500 },
          meta,
        }),
      ),
    );
    const result = await billingService.getLateFeePolicy();
    expect(result.data.grace_period_days).toBe(5);
  });

  it('updateLateFeePolicy puts late fee policy', async () => {
    server.use(
      http.put('/api/v1/billing/late-fee-policy', () =>
        HttpResponse.json({
          data: { grace_period_days: 7, fee_percent: 3, max_fee_cap: 600 },
          meta,
        }),
      ),
    );
    const result = await billingService.updateLateFeePolicy({
      grace_period_days: 7,
      fee_percent: 3,
      max_fee_cap: 600,
    });
    expect(result.data.fee_percent).toBe(3);
  });

  it('createPaymentPlan posts plan', async () => {
    const plan = {
      id: 'plan-1',
      student_id: 'student-1',
      name: 'Monthly Plan',
      total_amount: 10000,
      start_date: '2025-01-01',
      status: 'active',
      installments: [],
      created_at: new Date().toISOString(),
    };
    server.use(
      http.post('/api/v1/billing/payment-plans', () => HttpResponse.json({ data: plan, meta })),
    );
    const result = await billingService.createPaymentPlan({
      student_id: 'student-1',
      name: 'Monthly Plan',
      total_amount: 10000,
      start_date: '2025-01-01',
      installments: [],
    });
    expect(result.data.id).toBe('plan-1');
  });

  it('listPaymentPlans returns plans', async () => {
    server.use(
      http.get('/api/v1/billing/payment-plans', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await billingService.listPaymentPlans();
    expect(result.data).toEqual([]);
  });

  it('getPaymentPlan returns single plan', async () => {
    const plan = {
      id: 'plan-1',
      student_id: 'student-1',
      name: 'Monthly Plan',
      total_amount: 10000,
      start_date: '2025-01-01',
      status: 'active',
      installments: [],
      created_at: new Date().toISOString(),
    };
    server.use(
      http.get('/api/v1/billing/payment-plans/plan-1', () =>
        HttpResponse.json({ data: plan, meta }),
      ),
    );
    const result = await billingService.getPaymentPlan('plan-1');
    expect(result.data.id).toBe('plan-1');
  });
});

// ── budgetsService ────────────────────────────────────────────────────────────

describe('budgetsService', () => {
  const budget = {
    id: 'budget-1',
    name: 'Operations',
    total_amount: 50000,
    currency: 'MAD',
    academic_year_id: 'year-1',
    status: 'active',
    allocated_amount: 10000,
    remaining_amount: 40000,
  };

  const allocation = {
    id: 'alloc-1',
    budget_id: 'budget-1',
    category: 'supplies',
    amount: 5000,
    currency: 'MAD',
    status: 'active',
  };

  it('listBudgets returns budgets', async () => {
    server.use(
      http.get('/api/v1/budgets', () => HttpResponse.json({ data: [budget], meta: listMeta })),
    );
    const result = await budgetsService.listBudgets();
    expect(result.data).toHaveLength(1);
  });

  it('createBudget posts new budget', async () => {
    server.use(http.post('/api/v1/budgets', () => HttpResponse.json({ data: budget, meta })));
    const result = await budgetsService.createBudget({
      name: 'Operations',
      total_amount: 50000,
      currency: 'MAD',
      academic_year_id: 'year-1',
    });
    expect(result.data.id).toBe('budget-1');
  });

  it('getBudgetDetail returns budget detail', async () => {
    server.use(
      http.get('/api/v1/budgets/budget-1', () => HttpResponse.json({ data: budget, meta })),
    );
    const result = await budgetsService.getBudgetDetail('budget-1');
    expect(result.data.name).toBe('Operations');
  });

  it('updateBudget puts budget', async () => {
    server.use(
      http.put('/api/v1/budgets/budget-1', () =>
        HttpResponse.json({ data: { ...budget, name: 'Updated' }, meta }),
      ),
    );
    const result = await budgetsService.updateBudget('budget-1', { name: 'Updated' });
    expect(result.data.name).toBe('Updated');
  });

  it('deleteBudget deletes a budget', async () => {
    server.use(
      http.delete('/api/v1/budgets/budget-1', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await budgetsService.deleteBudget('budget-1');
    expect(result).toBeDefined();
  });

  it('getBudgetAllocations returns allocations', async () => {
    server.use(
      http.get('/api/v1/budgets/budget-1/allocations', () =>
        HttpResponse.json({ data: [allocation], meta }),
      ),
    );
    const result = await budgetsService.getBudgetAllocations('budget-1');
    expect(result.data).toHaveLength(1);
  });

  it('createAllocation posts allocation', async () => {
    server.use(
      http.post('/api/v1/budgets/budget-1/allocations', () =>
        HttpResponse.json({ data: allocation, meta }),
      ),
    );
    const result = await budgetsService.createAllocation('budget-1', {
      category: 'supplies',
      amount: 5000,
      currency: 'MAD',
    });
    expect(result.data.id).toBe('alloc-1');
  });

  it('getAllocation returns single allocation', async () => {
    server.use(
      http.get('/api/v1/budgets/allocations/alloc-1', () =>
        HttpResponse.json({ data: allocation, meta }),
      ),
    );
    const result = await budgetsService.getAllocation('alloc-1');
    expect(result.data.category).toBe('supplies');
  });

  it('updateAllocation puts allocation', async () => {
    server.use(
      http.put('/api/v1/budgets/allocations/alloc-1', () =>
        HttpResponse.json({ data: { ...allocation, amount: 6000 }, meta }),
      ),
    );
    const result = await budgetsService.updateAllocation('alloc-1', { amount: 6000 });
    expect(result.data.amount).toBe(6000);
  });

  it('getAllocationRequests returns requests', async () => {
    server.use(
      http.get('/api/v1/budgets/allocations/alloc-1/requests', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await budgetsService.getAllocationRequests('alloc-1');
    expect(result.data).toEqual([]);
  });

  it('approveBudgetRequest approves request', async () => {
    server.use(
      http.post('/api/v1/budgets/requests/req-1/approve', () =>
        HttpResponse.json({ data: { id: 'req-1', status: 'approved' }, meta }),
      ),
    );
    const result = await budgetsService.approveBudgetRequest('req-1', 'Approved');
    expect(result.data.status).toBe('approved');
  });

  it('rejectBudgetRequest rejects request', async () => {
    server.use(
      http.post('/api/v1/budgets/requests/req-1/reject', () =>
        HttpResponse.json({ data: { id: 'req-1', status: 'rejected' }, meta }),
      ),
    );
    const result = await budgetsService.rejectBudgetRequest('req-1', 'Not needed');
    expect(result.data.status).toBe('rejected');
  });

  it('getBudgetAnalytics returns analytics', async () => {
    server.use(
      http.get('/api/v1/budgets/analytics', () =>
        HttpResponse.json({ data: { total_budget: 50000, total_allocated: 10000 }, meta }),
      ),
    );
    const result = await budgetsService.getBudgetAnalytics();
    expect(result.data).toBeDefined();
  });

  it('getBudgetRequest returns single request', async () => {
    server.use(
      http.get('/api/v1/budgets/requests/req-1', () =>
        HttpResponse.json({ data: { id: 'req-1', status: 'pending' }, meta }),
      ),
    );
    const result = await budgetsService.getBudgetRequest('req-1');
    expect(result.data.id).toBe('req-1');
  });

  it('createTransaction posts transaction', async () => {
    server.use(
      http.post('/api/v1/budgets/allocations/alloc-1/transactions', () =>
        HttpResponse.json({ data: { id: 'txn-1', amount: 1000 }, meta }),
      ),
    );
    const result = await budgetsService.createTransaction('alloc-1', {
      amount: 1000,
      currency: 'MAD',
      description: 'Purchase',
      transaction_type: 'expense',
    });
    expect(result.data.id).toBe('txn-1');
  });

  it('getTransactions returns transactions', async () => {
    server.use(
      http.get('/api/v1/budgets/allocations/alloc-1/transactions', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await budgetsService.getTransactions('alloc-1');
    expect(result.data).toEqual([]);
  });
});

// ── invoicesService ───────────────────────────────────────────────────────────

describe('invoicesService', () => {
  const invoice = {
    id: 'inv-1',
    student_id: 'student-1',
    student_name: 'Alice',
    total_amount: 5000,
    currency: 'MAD',
    status: 'pending',
    issued_date: '2025-01-01',
    due_date: '2025-01-31',
  };

  it('listInvoices returns invoices', async () => {
    server.use(
      http.get('/api/v1/invoices', () => HttpResponse.json({ data: [invoice], meta: listMeta })),
    );
    const result = await invoicesService.listInvoices({});
    expect(result.data).toHaveLength(1);
  });

  it('getInvoiceDetail returns invoice detail', async () => {
    server.use(
      http.get('/api/v1/invoices/inv-1', () =>
        HttpResponse.json({ data: { ...invoice, items: [] }, meta }),
      ),
    );
    const result = await invoicesService.getInvoiceDetail('inv-1');
    expect(result.data.id).toBe('inv-1');
  });

  it('createPayment posts payment initiation', async () => {
    server.use(
      http.post('/api/v1/payments/initiate', () =>
        HttpResponse.json({
          data: {
            id: 'pay-1',
            invoice_id: 'inv-1',
            amount: 5000,
            method: 'cash',
            status: 'pending',
          },
          meta,
        }),
      ),
    );
    const result = await invoicesService.createPayment('inv-1', 5000, 'cash');
    expect(result.data.id).toBe('pay-1');
  });

  it('getInvoicePayments returns payments', async () => {
    server.use(http.get('/api/v1/payments/inv-1', () => HttpResponse.json({ data: [], meta })));
    const result = await invoicesService.getInvoicePayments('inv-1');
    expect(result.data).toEqual([]);
  });

  it('generateInvoicePdf posts pdf generation', async () => {
    server.use(
      http.post('/api/v1/invoices/inv-1/pdf', () =>
        HttpResponse.json({
          data: {
            id: 'job-1',
            type: 'invoice_pdf',
            status: 'pending',
            download_url: null,
            error_message: null,
          },
          meta,
        }),
      ),
    );
    const result = await invoicesService.generateInvoicePdf('inv-1', 'fr');
    expect(result.data.status).toBe('pending');
  });

  it('generatePaymentReceipt posts receipt generation', async () => {
    server.use(
      http.post('/api/v1/payments/pay-1/receipt', () =>
        HttpResponse.json({
          data: {
            id: 'job-2',
            type: 'receipt',
            status: 'pending',
            download_url: null,
            error_message: null,
          },
          meta,
        }),
      ),
    );
    const result = await invoicesService.generatePaymentReceipt('pay-1', 'fr');
    expect(result.data.type).toBe('receipt');
  });

  it('getReportJobStatus returns job status', async () => {
    server.use(
      http.get('/api/v1/reports/job-1/status', () =>
        HttpResponse.json({
          data: {
            id: 'job-1',
            type: 'invoice_pdf',
            status: 'ready',
            download_url: 'https://example.com/report',
            error_message: null,
          },
          meta,
        }),
      ),
    );
    const result = await invoicesService.getReportJobStatus('job-1');
    expect(result.data.status).toBe('ready');
  });
});
