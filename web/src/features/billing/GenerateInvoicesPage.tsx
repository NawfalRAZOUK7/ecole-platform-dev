import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatCurrency } from '@/shared/i18n';
import { useFeeStructures, useGenerateInvoices } from './useBilling';
import type { GenerateInvoicesResult } from './billing.service';

export function GenerateInvoicesPage() {
  const { t } = useTranslation();
  const feeStructuresQuery = useFeeStructures('ACTIVE');
  const generateInvoicesMutation = useGenerateInvoices();
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateInvoicesResult | null>(null);
  const [selectedFeeId, setSelectedFeeId] = useState('');
  const [periodId, setPeriodId] = useState('');
  const [issuedDate, setIssuedDate] = useState(new Date().toISOString().slice(0, 10));
  const [dueDate, setDueDate] = useState('');

  if (feeStructuresQuery.isLoading) {
    return <LoadingState />;
  }

  async function handleGenerate() {
    setError(null);
    setResult(null);

    try {
      const nextResult = await generateInvoicesMutation.mutateAsync({
        fee_structure_id: selectedFeeId,
        period_id: periodId || undefined,
        issued_date: issuedDate,
        due_date: dueDate,
      });
      setResult(nextResult);
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : t('app.error'));
    }
  }

  const feeStructures = feeStructuresQuery.data ?? [];

  return (
    <div className="page">
      <h1 className="page-title">{t('billing.generate.title')}</h1>

      <ErrorBanner
        error={error || (feeStructuresQuery.error instanceof Error ? feeStructuresQuery.error.message : null)}
        onDismiss={() => setError(null)}
        onRetry={() => void feeStructuresQuery.refetch()}
      />

      <div className="card" style={{ maxWidth: 600 }}>
        <div className="form-field">
          <label>{t('billing.generate.feeStructure')}</label>
          <select
            className="filter-select"
            value={selectedFeeId}
            onChange={(event) => setSelectedFeeId(event.target.value)}
          >
            <option value="">{t('billing.generate.selectFee')}</option>
            {feeStructures.map((feeStructure) => (
              <option key={feeStructure.id} value={feeStructure.id}>
                {feeStructure.name} ({formatCurrency(feeStructure.amount, feeStructure.currency)})
              </option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label>{t('billing.generate.periodId')}</label>
          <input
            type="text"
            value={periodId}
            onChange={(event) => setPeriodId(event.target.value)}
            placeholder="UUID"
          />
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <div className="form-field" style={{ flex: 1 }}>
            <label>{t('billing.generate.issuedDate')}</label>
            <input type="date" value={issuedDate} onChange={(event) => setIssuedDate(event.target.value)} />
          </div>
          <div className="form-field" style={{ flex: 1 }}>
            <label>{t('billing.generate.dueDate')}</label>
            <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
          </div>
        </div>

        <button
          className="btn btn-primary"
          style={{ marginTop: 16 }}
          onClick={handleGenerate}
          disabled={generateInvoicesMutation.isPending || !selectedFeeId || !dueDate}
        >
          {generateInvoicesMutation.isPending ? t('app.loading') : t('billing.generate.submit')}
        </button>
      </div>

      {result ? (
        <div className="card" style={{ maxWidth: 600, marginTop: 24 }}>
          <h3 style={{ marginBottom: 12 }}>{t('billing.generate.result')}</h3>
          <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <div className="stat-card">
              <div className="stat-value">{result.generated}</div>
              <div className="stat-label">{t('billing.generate.generated')}</div>
            </div>
            <div className="stat-card">
              <div
                className="stat-value"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {result.skipped}
              </div>
              <div className="stat-label">{t('billing.generate.skipped')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ fontSize: 22 }}>
                {formatCurrency(result.total_amount, result.currency)}
              </div>
              <div className="stat-label">{t('billing.generate.totalAmount')}</div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
