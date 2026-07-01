import { useMemo, useState } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { useTranslation } from 'react-i18next';
import { Badge, ConfirmDialog, DataTable, ErrorBanner, FormField, Pagination } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { BudgetEnvelope } from '../model/budgets.types';
import { useBudgets, useCreateBudget, useDeleteBudget } from '../model/useBudgets';

type BudgetTableRow = BudgetEnvelope & Record<string, unknown>;

const budgetFormSchema = z.object({
  name: z.string().min(2),
  total_amount: z.coerce.number().min(0),
  start_date: z.string().min(1),
  end_date: z.string().min(1),
});

type BudgetFormValues = z.infer<typeof budgetFormSchema>;

const madFormatter = new Intl.NumberFormat('fr-MA', {
  style: 'currency',
  currency: 'MAD',
});

function getBadgeVariant(status: string) {
  if (status === 'active') return 'success';
  if (status === 'frozen') return 'warning';
  return 'neutral';
}

export function BudgetListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [budgetToDelete, setBudgetToDelete] = useState<BudgetEnvelope | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const budgetsQuery = useBudgets({
    status: statusFilter || undefined,
  });
  const createBudgetMutation = useCreateBudget();
  const deleteBudgetMutation = useDeleteBudget();
  const methods = useForm<BudgetFormValues>({
    resolver: zodResolver(budgetFormSchema) as Resolver<BudgetFormValues>,
    defaultValues: {
      name: '',
      total_amount: 0,
      start_date: '',
      end_date: '',
    },
  });

  const filteredBudgets = useMemo(() => {
    return (budgetsQuery.data ?? []).filter((budget) => {
      const date = budget.created_at.slice(0, 10);
      return (!from || date >= from) && (!to || date <= to);
    });
  }, [budgetsQuery.data, from, to]);

  const totalPages = Math.max(1, Math.ceil(filteredBudgets.length / pageSize));
  const pageItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredBudgets.slice(start, start + pageSize);
  }, [currentPage, filteredBudgets, pageSize]);

  const columns: ColumnDef<BudgetTableRow>[] = useMemo(
    () => [
      { key: 'name', header: 'budgets.name' },
      {
        key: 'total_amount',
        header: 'budgets.totalAmount',
        render: (value) => madFormatter.format(Number(value)),
      },
      {
        key: 'spent_amount',
        header: 'budgets.spent',
        render: (value) => madFormatter.format(Number(value)),
      },
      {
        key: 'remaining_amount',
        header: 'budgets.remaining',
        render: (value) => madFormatter.format(Number(value)),
      },
      {
        key: 'status',
        header: 'budgets.status',
        render: (value) => <Badge variant={getBadgeVariant(String(value))}>{String(value)}</Badge>,
      },
      {
        key: 'id',
        header: 'budgets.actions',
        sortable: false,
        render: (_value, row) => (
          <div className="attendance-page__actions">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={(event) => {
                event.stopPropagation();
                navigate(`/budgets/${row.id}`);
              }}
            >
              {t('budgets.view')}
            </button>
            <button
              type="button"
              className="btn btn-danger btn-sm"
              onClick={(event) => {
                event.stopPropagation();
                setBudgetToDelete(row);
              }}
            >
              {t('budgets.delete')}
            </button>
          </div>
        ),
      },
    ],
    [navigate, t],
  );

  async function handleCreateBudget(values: BudgetFormValues) {
    await createBudgetMutation.mutateAsync(values);
    methods.reset();
    setShowCreateForm(false);
  }

  return (
    <div className="page budgets-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('budgets.title')}</h1>
          <p className="page-subtitle">{t('budgets.subtitle')}</p>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => setShowCreateForm((open) => !open)}
        >
          {t('budgets.createBudget')}
        </button>
      </div>

      <ErrorBanner
        error={toBannerError(
          budgetsQuery.error ?? createBudgetMutation.error ?? deleteBudgetMutation.error,
          t('app.error'),
        )}
      />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="">{t('budgets.allStatuses')}</option>
          <option value="active">{t('budgets.active')}</option>
          <option value="frozen">{t('budgets.frozen')}</option>
          <option value="closed">{t('budgets.closed')}</option>
        </select>
        <input
          type="date"
          className="filter-input"
          value={from}
          onChange={(event) => setFrom(event.target.value)}
        />
        <input
          type="date"
          className="filter-input"
          value={to}
          onChange={(event) => setTo(event.target.value)}
        />
      </div>

      {showCreateForm && (
        <FormProvider {...methods}>
          <form
            className="card budgets-page__form"
            onSubmit={methods.handleSubmit(handleCreateBudget)}
          >
            <FormField<BudgetFormValues> name="name" label="budgets.name" />
            <FormField<BudgetFormValues>
              name="total_amount"
              label="budgets.totalAmount"
              type="number"
            />
            <FormField<BudgetFormValues> name="start_date" label="budgets.startDate" type="date" />
            <FormField<BudgetFormValues> name="end_date" label="budgets.endDate" type="date" />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createBudgetMutation.isPending}
            >
              {createBudgetMutation.isPending ? t('app.loading') : t('budgets.saveBudget')}
            </button>
          </form>
        </FormProvider>
      )}

      <DataTable
        columns={columns}
        data={pageItems as BudgetTableRow[]}
        loading={budgetsQuery.isLoading}
        emptyMessage="budgets.empty"
        ariaLabel={t('budgets.title')}
        onRowClick={(row) => navigate(`/budgets/${row.id}`)}
      />

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setCurrentPage(1);
        }}
      />

      <ConfirmDialog
        open={Boolean(budgetToDelete)}
        title="budgets.deleteBudget"
        message="budgets.deleteBudgetConfirm"
        confirmLabel="budgets.delete"
        variant="danger"
        loading={deleteBudgetMutation.isPending}
        onCancel={() => setBudgetToDelete(null)}
        onConfirm={() => {
          if (!budgetToDelete) {
            return;
          }
          void deleteBudgetMutation.mutateAsync(budgetToDelete.id).then(() => {
            setBudgetToDelete(null);
          });
        }}
      />
    </div>
  );
}
