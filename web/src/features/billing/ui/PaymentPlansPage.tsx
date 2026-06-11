import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/shared/ui/Badge';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';
import { usePaymentPlans, useCreatePaymentPlan } from '../model/useBilling';
import type { PaymentPlanInput } from '../api/billing.api';

const STATUS_VARIANT: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
  active: 'success',
  completed: 'info',
  cancelled: 'error',
};

function formatMAD(amount: number | null | undefined) {
  return new Intl.NumberFormat('fr-MA', { style: 'currency', currency: 'MAD' }).format(amount ?? 0);
}

function planTitle(plan: { name?: string; invoice_number?: string; id: string }) {
  return plan.name ?? plan.invoice_number ?? plan.id.slice(0, 8);
}

interface PlanForm {
  invoice_id: string;
  num_installments: string;
}

const EMPTY_FORM: PlanForm = {
  invoice_id: '',
  num_installments: '3',
};

export function PaymentPlansPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const plansQuery = usePaymentPlans();
  const createMutation = useCreatePaymentPlan();
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<PlanForm>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const plans = plansQuery.data ?? [];

  async function handleCreate() {
    setError(null);
    const payload: PaymentPlanInput = {
      invoice_id: form.invoice_id,
      num_installments: Number.parseInt(form.num_installments, 10),
    };
    try {
      await createMutation.mutateAsync(payload);
      setShowModal(false);
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (plansQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <h1 className="page-title" style={{ marginBottom: 0 }}>
          {t('billing.paymentPlans.title')}
        </h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + {t('billing.paymentPlans.create')}
        </button>
      </div>

      <ErrorBanner
        error={error || (plansQuery.error instanceof Error ? plansQuery.error.message : null)}
        onDismiss={() => setError(null)}
        onRetry={() => void plansQuery.refetch()}
      />

      {plans.length === 0 ? (
        <EmptyState message={t('billing.paymentPlans.empty')} icon="💳" />
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('billing.paymentPlans.planName')}</th>
                <th>{t('billing.paymentPlans.student')}</th>
                <th>{t('billing.paymentPlans.totalAmount')}</th>
                <th>{t('billing.paymentPlans.installments')}</th>
                <th>{t('billing.paymentPlans.startDate')}</th>
                <th>{t('billing.paymentPlans.status')}</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((plan) => (
                <tr
                  key={plan.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => void navigate(`/billing/payment-plans/${plan.id}`)}
                >
                  <td>{planTitle(plan)}</td>
                  <td>{plan.student_name ?? plan.student_id}</td>
                  <td>{formatMAD(plan.total_amount ?? plan.invoice_total_amount)}</td>
                  <td>{plan.installments?.length ?? plan.total_installments ?? 0}</td>
                  <td>{formatDate(plan.start_date ?? plan.issued_date, i18n.language)}</td>
                  <td>
                    <Badge variant={STATUS_VARIANT[plan.status] ?? 'info'}>
                      {t(`billing.paymentPlans.statuses.${plan.status}`, plan.status)}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div
            className="modal-card"
            style={{ maxWidth: 560 }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginBottom: 16 }}>{t('billing.paymentPlans.create')}</h2>

            <div className="form-field">
              <label>{t('billing.paymentPlans.invoiceId', 'ID de la facture')}</label>
              <input
                type="text"
                value={form.invoice_id}
                onChange={(e) => setForm({ ...form, invoice_id: e.target.value })}
                placeholder="UUID"
              />
            </div>

            <div className="form-field">
              <label>{t('billing.paymentPlans.numInstallments', "Nombre d'echeances")}</label>
              <input
                type="number"
                min={1}
                max={24}
                value={form.num_installments}
                onChange={(e) => setForm({ ...form, num_installments: e.target.value })}
              />
            </div>

            {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={createMutation.isPending || !form.invoice_id || !form.num_installments}
              >
                {createMutation.isPending ? t('app.loading') : t('app.save')}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowModal(false)}
              >
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
