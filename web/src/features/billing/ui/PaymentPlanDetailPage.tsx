import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Badge } from '@/shared/ui/Badge';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';
import { usePaymentPlan } from '../model/useBilling';

const STATUS_VARIANT: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
  active: 'success',
  completed: 'info',
  cancelled: 'error',
  paid: 'success',
  pending: 'warning',
  overdue: 'error',
};

function formatMAD(amount: number) {
  return new Intl.NumberFormat('fr-MA', { style: 'currency', currency: 'MAD' }).format(amount);
}

export function PaymentPlanDetailPage() {
  const { planId } = useParams<{ planId: string }>();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const planQuery = usePaymentPlan(planId ?? '');

  if (planQuery.isLoading) return <LoadingState />;
  if (planQuery.error) {
    return (
      <div className="page">
        <ErrorBanner
          error={planQuery.error instanceof Error ? planQuery.error.message : t('app.error')}
          onRetry={() => void planQuery.refetch()}
        />
      </div>
    );
  }

  const plan = planQuery.data;
  if (!plan) {
    return (
      <div className="page">
        <EmptyState message={t('billing.paymentPlans.notFound')} icon="🔎" />
      </div>
    );
  }

  const paidTotal = plan.installments
    .filter((inst) => inst.status === 'paid')
    .reduce((acc, inst) => acc + inst.amount, 0);
  const progressPercent =
    plan.total_amount > 0 ? Math.min(100, Math.round((paidTotal / plan.total_amount) * 100)) : 0;

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => void navigate('/billing/payment-plans')}
        >
          ← {t('app.back')}
        </button>
        <h1 className="page-title" style={{ marginBottom: 0 }}>
          {plan.name}
        </h1>
        <Badge variant={STATUS_VARIANT[plan.status] ?? 'info'}>
          {t(`billing.paymentPlans.statuses.${plan.status}`, plan.status)}
        </Badge>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 16,
          }}
        >
          <div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>
              {t('billing.paymentPlans.student')}
            </p>
            <p style={{ fontWeight: 600 }}>{plan.student_name ?? plan.student_id}</p>
          </div>
          <div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>
              {t('billing.paymentPlans.totalAmount')}
            </p>
            <p style={{ fontWeight: 600 }}>{formatMAD(plan.total_amount)}</p>
          </div>
          <div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>
              {t('billing.paymentPlans.startDate')}
            </p>
            <p style={{ fontWeight: 600 }}>{formatDate(plan.start_date, i18n.language)}</p>
          </div>
          <div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>
              {t('billing.paymentPlans.createdAt')}
            </p>
            <p style={{ fontWeight: 600 }}>{formatDate(plan.created_at, i18n.language)}</p>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <p style={{ marginBottom: 8 }}>
          <strong>{t('billing.paymentPlans.progress')}</strong>
          {' — '}
          {formatMAD(paidTotal)} / {formatMAD(plan.total_amount)}
          {' ('}
          {progressPercent}
          {'%)'}
        </p>
        <div
          style={{
            height: 12,
            background: 'var(--color-surface-2)',
            borderRadius: 6,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${progressPercent}%`,
              background: progressPercent === 100 ? 'var(--color-success)' : 'var(--color-primary)',
              borderRadius: 6,
              transition: 'width 0.3s',
            }}
          />
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: 16 }}>{t('billing.paymentPlans.installmentsLabel')}</h2>
        {plan.installments.length === 0 ? (
          <EmptyState message={t('billing.paymentPlans.noInstallments')} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>{t('billing.paymentPlans.dueDate')}</th>
                <th>{t('billing.paymentPlans.amount')}</th>
                <th>{t('billing.paymentPlans.status')}</th>
                <th>{t('billing.paymentPlans.paidAt')}</th>
              </tr>
            </thead>
            <tbody>
              {plan.installments.map((inst, index) => (
                <tr key={inst.id}>
                  <td>{index + 1}</td>
                  <td>{formatDate(inst.due_date, i18n.language)}</td>
                  <td>{formatMAD(inst.amount)}</td>
                  <td>
                    <Badge variant={STATUS_VARIANT[inst.status] ?? 'info'}>
                      {t(`billing.paymentPlans.installmentStatuses.${inst.status}`, inst.status)}
                    </Badge>
                  </td>
                  <td>{inst.paid_at ? formatDate(inst.paid_at, i18n.language) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
