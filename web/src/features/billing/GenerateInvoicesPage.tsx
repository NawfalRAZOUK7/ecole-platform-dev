/**
 * Generate Invoices page — generate invoices from fee structures (ADM).
 *
 * Reference: Phase 12A — Billing Management
 * Calls POST /billing/generate-invoices.
 */

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { formatCurrency } from '@/shared/i18n';

interface FeeStructure {
  id: string;
  name: string;
  amount: number;
  currency: string;
  status: string;
}

interface GenerateResult {
  generated: number;
  skipped: number;
  total_amount: number;
  currency: string;
}

export function GenerateInvoicesPage() {
  const { t } = useTranslation();
  const [feeStructures, setFeeStructures] = useState<FeeStructure[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<GenerateResult | null>(null);

  const [selectedFeeId, setSelectedFeeId] = useState('');
  const [periodId, setPeriodId] = useState('');
  const [issuedDate, setIssuedDate] = useState(new Date().toISOString().slice(0, 10));
  const [dueDate, setDueDate] = useState('');

  useEffect(() => {
    api.list<FeeStructure>('/billing/fee-structures', { status: 'ACTIVE' })
      .then((r) => setFeeStructures(r.data))
      .catch(() => {});
  }, []);

  async function handleGenerate() {
    setSaving(true);
    setResult(null);
    try {
      const resp = await api.post<GenerateResult>('/billing/generate-invoices', {
        fee_structure_id: selectedFeeId,
        period_id: periodId || undefined,
        issued_date: issuedDate,
        due_date: dueDate,
      });
      setResult(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('billing.generate.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="card" style={{ maxWidth: 600 }}>
        <div className="form-field">
          <label>{t('billing.generate.feeStructure')}</label>
          <select className="filter-select" value={selectedFeeId} onChange={(e) => setSelectedFeeId(e.target.value)}>
            <option value="">{t('billing.generate.selectFee')}</option>
            {feeStructures.map((f) => (
              <option key={f.id} value={f.id}>{f.name} ({formatCurrency(f.amount, f.currency)})</option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label>{t('billing.generate.periodId')}</label>
          <input
            type="text"
            value={periodId}
            onChange={(e) => setPeriodId(e.target.value)}
            placeholder="UUID"
          />
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <div className="form-field" style={{ flex: 1 }}>
            <label>{t('billing.generate.issuedDate')}</label>
            <input type="date" value={issuedDate} onChange={(e) => setIssuedDate(e.target.value)} />
          </div>
          <div className="form-field" style={{ flex: 1 }}>
            <label>{t('billing.generate.dueDate')}</label>
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </div>
        </div>

        <button
          className="btn btn-primary"
          style={{ marginTop: 16 }}
          onClick={handleGenerate}
          disabled={saving || !selectedFeeId || !dueDate}
        >
          {saving ? t('app.loading') : t('billing.generate.submit')}
        </button>
      </div>

      {result && (
        <div className="card" style={{ maxWidth: 600, marginTop: 24 }}>
          <h3 style={{ marginBottom: 12 }}>{t('billing.generate.result')}</h3>
          <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <div className="stat-card">
              <div className="stat-value">{result.generated}</div>
              <div className="stat-label">{t('billing.generate.generated')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: 'var(--color-text-secondary)' }}>{result.skipped}</div>
              <div className="stat-label">{t('billing.generate.skipped')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ fontSize: 22 }}>{formatCurrency(result.total_amount, result.currency)}</div>
              <div className="stat-label">{t('billing.generate.totalAmount')}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
