import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { useAuth } from '@/services/auth/AuthContext';
import { ConfirmDialog, DataTable, ErrorBanner, Tabs } from '@/shared/ui';
import { formatDate } from '@/shared/i18n';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { BudgetAllocation, BudgetRequest, BudgetTransaction } from './budgets.types';
import {
  useApproveBudgetRequest,
  useBudgetAllocations,
  useBudgetDetail,
  useBudgetRequests,
  useBudgetTransactions,
  useRejectBudgetRequest,
} from './useBudgets';

type BudgetAllocationRow = BudgetAllocation & Record<string, unknown>;
type BudgetTransactionRow = BudgetTransaction & Record<string, unknown>;
type BudgetRequestRow = BudgetRequest & Record<string, unknown>;

const madFormatter = new Intl.NumberFormat('fr-MA', {
  style: 'currency',
  currency: 'MAD',
});

const PIE_COLORS = ['var(--color-primary)', 'var(--color-success)', 'var(--color-warning)', 'var(--color-error)', 'var(--color-secondary)'];

export function BudgetDetailPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const { id = '' } = useParams();
  const [pendingReview, setPendingReview] = useState<{
    requestId: string;
    action: 'approve' | 'reject';
  } | null>(null);

  const budgetDetailQuery = useBudgetDetail(id);
  const allocationsQuery = useBudgetAllocations(id);
  const transactionsQuery = useBudgetTransactions(id);
  const requestsQuery = useBudgetRequests({ budget_id: id, status: 'pending' });
  const approveRequestMutation = useApproveBudgetRequest();
  const rejectRequestMutation = useRejectBudgetRequest();

  const allocationsColumns: ColumnDef<BudgetAllocationRow>[] = useMemo(
    () => [
      { key: 'label', header: 'budgets.name' },
      { key: 'category', header: 'budgets.category' },
      {
        key: 'amount',
        header: 'budgets.totalAmount',
        render: (value) => madFormatter.format(Number(value)),
      },
      {
        key: 'remaining',
        header: 'budgets.remaining',
        render: (value) => madFormatter.format(Number(value)),
      },
    ],
    []
  );

  const transactionColumns: ColumnDef<BudgetTransactionRow>[] = useMemo(
    () => [
      {
        key: 'date',
        header: 'budgets.date',
        render: (value) => formatDate(String(value), i18n.language),
      },
      {
        key: 'amount',
        header: 'budgets.totalAmount',
        render: (value) => madFormatter.format(Number(value)),
      },
      { key: 'type', header: 'budgets.type' },
      { key: 'description', header: 'budgets.description' },
    ],
    [i18n.language]
  );

  const requestColumns: ColumnDef<BudgetRequestRow>[] = useMemo(
    () => [
      { key: 'requester_name', header: 'budgets.requester', render: (value) => String(value ?? '—') },
      {
        key: 'amount',
        header: 'budgets.totalAmount',
        render: (value) => madFormatter.format(Number(value)),
      },
      { key: 'category', header: 'budgets.category' },
      { key: 'justification', header: 'budgets.justification' },
      {
        key: 'id',
        header: 'budgets.actions',
        sortable: false,
        render: (_value, row) =>
          user?.role === 'DIR' ? (
            <div className="attendance-page__actions">
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => setPendingReview({ requestId: row.id, action: 'approve' })}
              >
                {t('budgets.approve')}
              </button>
              <button
                type="button"
                className="btn btn-danger btn-sm"
                onClick={() => setPendingReview({ requestId: row.id, action: 'reject' })}
              >
                {t('budgets.reject')}
              </button>
            </div>
          ) : null,
      },
    ],
    [t, user?.role]
  );

  return (
    <div className="page budget-detail-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{budgetDetailQuery.data?.name ?? t('budgets.title')}</h1>
          <p className="page-subtitle">
            {madFormatter.format(budgetDetailQuery.data?.total_amount ?? 0)} · {formatDate(budgetDetailQuery.data?.start_date ?? '', i18n.language)} → {formatDate(budgetDetailQuery.data?.end_date ?? '', i18n.language)}
          </p>
        </div>
      </div>

      <ErrorBanner
        error={toBannerError(
          budgetDetailQuery.error ??
            allocationsQuery.error ??
            transactionsQuery.error ??
            requestsQuery.error ??
            approveRequestMutation.error ??
            rejectRequestMutation.error,
          t('app.error')
        )}
      />

      <div className="card budgets-page__chart">
        <h2 className="attendance-page__section-title">{t('budgets.allocationBreakdown')}</h2>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={allocationsQuery.data ?? []}
              dataKey="amount"
              nameKey="label"
              outerRadius={110}
              label
            >
              {(allocationsQuery.data ?? []).map((entry, index) => (
                <Cell key={entry.id} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value: number) => madFormatter.format(value)} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <Tabs
        defaultTab="allocations"
        tabs={[
          {
            id: 'allocations',
            label: 'budgets.allocations',
            content: (
              <DataTable
                columns={allocationsColumns}
                data={(allocationsQuery.data ?? []) as BudgetAllocationRow[]}
                loading={allocationsQuery.isLoading}
                emptyMessage="budgets.empty"
                ariaLabel={t('budgets.allocations')}
              />
            ),
          },
          {
            id: 'transactions',
            label: 'budgets.transactions',
            content: (
              <DataTable
                columns={transactionColumns}
                data={(transactionsQuery.data ?? []) as BudgetTransactionRow[]}
                loading={transactionsQuery.isLoading}
                emptyMessage="budgets.empty"
                ariaLabel={t('budgets.transactions')}
              />
            ),
          },
          {
            id: 'requests',
            label: 'budgets.requests',
            content: (
              <DataTable
                columns={requestColumns}
                data={(requestsQuery.data ?? []) as BudgetRequestRow[]}
                loading={requestsQuery.isLoading}
                emptyMessage="budgets.empty"
                ariaLabel={t('budgets.requests')}
              />
            ),
          },
        ]}
      />

      <ConfirmDialog
        open={Boolean(pendingReview)}
        title={
          pendingReview?.action === 'approve'
            ? 'budgets.approveRequestTitle'
            : 'budgets.rejectRequestTitle'
        }
        message={
          pendingReview?.action === 'approve'
            ? 'budgets.approveRequestConfirm'
            : 'budgets.rejectRequestConfirm'
        }
        confirmLabel={
          pendingReview?.action === 'approve' ? 'budgets.approve' : 'budgets.reject'
        }
        variant={pendingReview?.action === 'approve' ? 'info' : 'warning'}
        loading={approveRequestMutation.isPending || rejectRequestMutation.isPending}
        onCancel={() => setPendingReview(null)}
        onConfirm={() => {
          if (!pendingReview) {
            return;
          }

          const mutation =
            pendingReview.action === 'approve'
              ? approveRequestMutation.mutateAsync({ requestId: pendingReview.requestId })
              : rejectRequestMutation.mutateAsync({ requestId: pendingReview.requestId });

          void mutation.then(() => {
            setPendingReview(null);
          });
        }}
      />
    </div>
  );
}
