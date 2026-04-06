import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { useSiblingPolicy, useUpdateSiblingPolicy } from './useBilling';

const siblingSchema = z.object({
  max_siblings_covered: z.number().int().min(1).max(10),
  discounts: z.array(
    z.object({
      sibling_rank: z.number().int().min(2),
      discount_percent: z.number().min(0).max(100),
    })
  ),
});

type SiblingFormValues = z.infer<typeof siblingSchema>;

export function SiblingPolicyPage() {
  const { t } = useTranslation();
  const policyQuery = useSiblingPolicy();
  const updateMutation = useUpdateSiblingPolicy();
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm<SiblingFormValues>({
    resolver: zodResolver(siblingSchema),
    defaultValues: { max_siblings_covered: 3, discounts: [] },
  });

  const maxSiblings = watch('max_siblings_covered');
  const discounts = watch('discounts');

  useEffect(() => {
    if (policyQuery.data) {
      reset(policyQuery.data);
    }
  }, [policyQuery.data, reset]);

  useEffect(() => {
    const rows: Array<{ sibling_rank: number; discount_percent: number }> = [];
    for (let i = 2; i <= maxSiblings; i++) {
      const existing = discounts.find((d) => d.sibling_rank === i);
      rows.push({ sibling_rank: i, discount_percent: existing?.discount_percent ?? 0 });
    }
    setValue('discounts', rows);
  }, [maxSiblings, setValue]);

  async function onSubmit(values: SiblingFormValues) {
    setError(null);
    setSaved(false);
    try {
      await updateMutation.mutateAsync(values);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (policyQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('billing.siblingPolicy.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />
      {saved && (
        <div className="alert alert-success" style={{ marginBottom: 16 }}>
          {t('app.saved')}
        </div>
      )}

      <div className="card" style={{ maxWidth: 600 }}>
        <p style={{ marginBottom: 16 }}>{t('billing.siblingPolicy.description')}</p>

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="form-field">
            <label>{t('billing.siblingPolicy.maxSiblings')}</label>
            <input
              type="number"
              min={1}
              max={10}
              {...register('max_siblings_covered', { valueAsNumber: true })}
            />
            {errors.max_siblings_covered && (
              <span className="form-error">{errors.max_siblings_covered.message}</span>
            )}
          </div>

          <table className="data-table" style={{ marginBottom: 16 }}>
            <thead>
              <tr>
                <th>{t('billing.siblingPolicy.siblingRank')}</th>
                <th>{t('billing.siblingPolicy.discountPercent')}</th>
              </tr>
            </thead>
            <tbody>
              {discounts.map((row, index) => (
                <tr key={row.sibling_rank}>
                  <td>{t('billing.siblingPolicy.siblingN', { n: row.sibling_rank })}</td>
                  <td>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step={0.1}
                      style={{ width: 80 }}
                      {...register(`discounts.${index}.discount_percent`, { valueAsNumber: true })}
                    />
                    {' %'}
                    {errors.discounts?.[index]?.discount_percent && (
                      <span className="form-error">
                        {errors.discounts[index].discount_percent?.message}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

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
