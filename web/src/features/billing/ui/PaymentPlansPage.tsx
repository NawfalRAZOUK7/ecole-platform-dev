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

interface InstallmentRow {
  due_date: string;
  amount: string;
}

interface PlanForm {
  student_id: string;
  name: string;
  total_amount: string;
  start_date: string;
  installments: InstallmentRow[];
}

const EMPTY_FORM: PlanForm = {
  student_id: '',
  name: '',
  total_amount: '',
  start_date: new Date().toISOString().split('T')[0],
  installments: [{ due_date: '', amount: '' }],
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

  function addInstallment() {
    setForm((prev) => ({
      ...prev,
      installments: [...prev.installments, { due_date: '', amount: '' }],
    }));
  }

  function removeInstallment(index: number) {
    setForm((prev) => ({
      ...prev,
      installments: prev.installments.filter((_, i) => i !== index),
    }));
  }

  function setInstallment(index: number, field: keyof InstallmentRow, value: string) {
    setForm((prev) => {
      const next = [...prev.installments];
      next[index] = { ...next[index], [field]: value };
      return { ...prev, installments: next };
    });
  }

  async function handleCreate() {
    setError(null);
    const payload: PaymentPlanInput = {
      student_id: form.student_id,
      name: form.name,
      total_amount: Number.parseFloat(form.total_amount),
      start_date: form.start_date,
      installments: form.installments.map((row) => ({
        due_date: row.due_date,
        amount: Number.parseFloat(row.amount),
      })),
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
                  <td>{plan.name}</td>
                  <td>{plan.student_name ?? plan.student_id}</td>
                  <td>
                    {new Intl.NumberFormat('fr-MA', { style: 'currency', currency: 'MAD' }).format(
                      plan.total_amount,
                    )}
                  </td>
                  <td>{plan.installments.length}</td>
                  <td>{formatDate(plan.start_date, i18n.language)}</td>
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
              <label>{t('billing.paymentPlans.planName')}</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>

            <div className="form-field">
              <label>{t('billing.paymentPlans.studentId')}</label>
              <input
                type="text"
                value={form.student_id}
                onChange={(e) => setForm({ ...form, student_id: e.target.value })}
                placeholder="UUID"
              />
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.paymentPlans.totalAmount')} (MAD)</label>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  value={form.total_amount}
                  onChange={(e) => setForm({ ...form, total_amount: e.target.value })}
                />
              </div>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.paymentPlans.startDate')}</label>
                <input
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                />
              </div>
            </div>

            <div style={{ marginBottom: 12 }}>
              <strong>{t('billing.paymentPlans.installmentsLabel')}</strong>
              {form.installments.map((row, index) => (
                <div
                  key={index}
                  style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center' }}
                >
                  <input
                    type="date"
                    value={row.due_date}
                    style={{ flex: 1 }}
                    onChange={(e) => setInstallment(index, 'due_date', e.target.value)}
                    placeholder={t('billing.paymentPlans.dueDate')}
                  />
                  <input
                    type="number"
                    min={0}
                    step={0.01}
                    value={row.amount}
                    style={{ width: 100 }}
                    onChange={(e) => setInstallment(index, 'amount', e.target.value)}
                    placeholder="MAD"
                  />
                  {form.installments.length > 1 && (
                    <button
                      type="button"
                      className="btn btn-sm btn-secondary"
                      onClick={() => removeInstallment(index)}
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                style={{ marginTop: 8 }}
                onClick={addInstallment}
              >
                + {t('billing.paymentPlans.addInstallment')}
              </button>
            </div>

            {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={createMutation.isPending || !form.name || !form.student_id}
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
