import { useMemo } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, FormField, FormTextarea } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { BudgetRequest } from './budgets.types';
import { useBudgetRequests, useCreateBudgetRequest } from './useBudgets';

type BudgetRequestRow = BudgetRequest & Record<string, unknown>;

const requestSchema = z.object({
  amount: z.coerce.number().gt(0),
  category: z.string().min(2),
  justification: z.string().min(5),
});

type RequestFormValues = z.infer<typeof requestSchema>;

const madFormatter = new Intl.NumberFormat('fr-MA', {
  style: 'currency',
  currency: 'MAD',
});

export function BudgetRequestPage() {
  const { t } = useTranslation();
  const requestsQuery = useBudgetRequests({ status: 'pending', mine: 'true' });
  const createRequestMutation = useCreateBudgetRequest();
  const methods = useForm<RequestFormValues>({
    resolver: zodResolver(requestSchema) as Resolver<RequestFormValues>,
    defaultValues: {
      amount: 0,
      category: '',
      justification: '',
    },
  });

  const columns: ColumnDef<BudgetRequestRow>[] = useMemo(
    () => [
      { key: 'category', header: 'budgets.category' },
      {
        key: 'amount',
        header: 'budgets.totalAmount',
        render: (value) => madFormatter.format(Number(value)),
      },
      { key: 'status', header: 'budgets.status' },
      { key: 'justification', header: 'budgets.justification' },
    ],
    []
  );

  async function handleSubmit(values: RequestFormValues) {
    await createRequestMutation.mutateAsync({
      amount: values.amount,
      category: values.category,
      justification: values.justification,
      description: values.category,
    });
    methods.reset();
  }

  return (
    <div className="page budgets-request-page">
      <div className="page-header">
        <h1 className="page-title">{t('budgets.requests')}</h1>
      </div>

      <ErrorBanner error={toBannerError(requestsQuery.error ?? createRequestMutation.error, t('app.error'))} />

      <FormProvider {...methods}>
        <form className="card budgets-page__form" onSubmit={methods.handleSubmit(handleSubmit)}>
          <FormField<RequestFormValues> name="amount" label="budgets.totalAmount" type="number" />
          <FormField<RequestFormValues> name="category" label="budgets.category" />
          <FormTextarea<RequestFormValues> name="justification" label="budgets.justification" rows={4} />
          <button type="submit" className="btn btn-primary" disabled={createRequestMutation.isPending}>
            {createRequestMutation.isPending ? t('app.loading') : t('budgets.submitRequest')}
          </button>
        </form>
      </FormProvider>

      <DataTable
        columns={columns}
        data={(requestsQuery.data ?? []) as BudgetRequestRow[]}
        loading={requestsQuery.isLoading}
        emptyMessage="budgets.empty"
        ariaLabel={t('budgets.requests')}
      />
    </div>
  );
}
