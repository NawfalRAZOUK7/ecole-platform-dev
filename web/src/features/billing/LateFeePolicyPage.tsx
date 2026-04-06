import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { formatCurrency } from '@/shared/i18n';
import { useLateFeePolicy, useUpdateLateFeePolicy } from './useBilling';

const lateFeePolicySchema = z.object({
  grace_period_days: z.number().int().min(0).max(90),
  fee_percent: z.number().min(0).max(100),
  max_fee_cap: z.number().min(0),
});

type LateFeePolicyFormValues = z.infer<typeof lateFeePolicySchema>;

export function LateFeePolicyPage() {
  const { t } = useTranslation();
  const policyQuery = useLateFeePolicy();
  const updateMutation = useUpdateLateFeePolicy();
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<LateFeePolicyFormValues>({
    resolver: zodResolver(lateFeePolicySchema),
    defaultValues: { grace_period_days: 5, fee_percent: 1.5, max_fee_cap: 500 },
  });

  const values = watch();

  useEffect(() => {
    if (policyQuery.data) {
      reset({
        grace_period_days: policyQuery.data.grace_period_days,
        fee_percent: policyQuery.data.fee_percent,
        max_fee_cap: policyQuery.data.max_fee_cap,
      });
    }
  }, [policyQuery.data, reset]);

  async function onSubmit(formValues: LateFeePolicyFormValues) {
    setError(null);
    setSaved(false);
    try {
      await updateMutation.mutateAsync(formValues);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (policyQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('billing.lateFeePolicy.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {saved && (
        <div className="alert alert-success" style={{ marginBottom: 16 }}>
          {t('app.saved')}
        </div>
      )}

      <div className="card" style={{ maxWidth: 560 }}>
        <p style={{ marginBottom: 16 }}>{t('billing.lateFeePolicy.description')}</p>

        {policyQuery.data && (
          <div className="card" style={{ background: 'var(--color-surface-2)', marginBottom: 20 }}>
            <p>
              <strong>{t('billing.lateFeePolicy.gracePeriodDays')}:</strong>{' '}
              {policyQuery.data.grace_period_days} {t('billing.lateFeePolicy.days')}
            </p>
            <p>
              <strong>{t('billing.lateFeePolicy.feePercent')}:</strong>{' '}
              {policyQuery.data.fee_percent} %
            </p>
            <p>
              <strong>{t('billing.lateFeePolicy.maxFeeCap')}:</strong>{' '}
              {formatCurrency(policyQuery.data.max_fee_cap)}
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="form-field">
            <label>{t('billing.lateFeePolicy.gracePeriodDays')}</label>
            <input
              type="number"
              min={0}
              max={90}
              {...register('grace_period_days', { valueAsNumber: true })}
            />
            {errors.grace_period_days && (
              <span className="form-error">{errors.grace_period_days.message}</span>
            )}
          </div>

          <div className="form-field">
            <label>{t('billing.lateFeePolicy.feePercent')}</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="number"
                min={0}
                max={100}
                step={0.1}
                style={{ width: 100 }}
                {...register('fee_percent', { valueAsNumber: true })}
              />
              <span>%</span>
            </div>
            {errors.fee_percent && (
              <span className="form-error">{errors.fee_percent.message}</span>
            )}
          </div>

          <div className="form-field">
            <label>{t('billing.lateFeePolicy.maxFeeCap')} (MAD)</label>
            <input
              type="number"
              min={0}
              step={0.01}
              {...register('max_fee_cap', { valueAsNumber: true })}
            />
            {errors.max_fee_cap && (
              <span className="form-error">{errors.max_fee_cap.message}</span>
            )}
            {values.max_fee_cap > 0 && (
              <small style={{ color: 'var(--color-text-secondary)' }}>
                = {formatCurrency(values.max_fee_cap)}
              </small>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? t('app.loading') : t('app.save')}
          </button>
        </form>
      </div>
    </div>
  );
}
