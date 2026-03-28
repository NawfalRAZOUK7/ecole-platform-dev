import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatCurrency } from '@/shared/i18n';
import {
  useCreateFeeStructure,
  useFeeStructures,
  useUpdateFeeStructure,
} from './useBilling';
import type { FeeStructure } from './billing.service';

interface FeeForm {
  academic_year_id: string;
  name: string;
  amount: string;
  currency: string;
  frequency: string;
  due_day: string;
  applies_to_level: string;
}

const EMPTY_FEE_FORM: FeeForm = {
  academic_year_id: '',
  name: '',
  amount: '',
  currency: 'MAD',
  frequency: 'monthly',
  due_day: '5',
  applies_to_level: '',
};

export function FeeStructuresPage() {
  const { t } = useTranslation();
  const feeStructuresQuery = useFeeStructures();
  const createFeeStructureMutation = useCreateFeeStructure();
  const updateFeeStructureMutation = useUpdateFeeStructure();
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FeeForm>(EMPTY_FEE_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);

  if (feeStructuresQuery.isLoading) {
    return <LoadingState />;
  }

  const items = feeStructuresQuery.data ?? [];
  const saving = createFeeStructureMutation.isPending || updateFeeStructureMutation.isPending;

  function openCreate() {
    setForm(EMPTY_FEE_FORM);
    setEditingId(null);
    setShowForm(true);
    setError(null);
  }

  function openEdit(item: FeeStructure) {
    setForm({
      academic_year_id: item.academic_year_id,
      name: item.name,
      amount: String(item.amount),
      currency: item.currency,
      frequency: item.frequency,
      due_day: String(item.due_day),
      applies_to_level: item.applies_to_level || '',
    });
    setEditingId(item.id);
    setShowForm(true);
    setError(null);
  }

  async function handleSave() {
    setError(null);

    const payload = {
      academic_year_id: form.academic_year_id || undefined,
      name: form.name,
      amount: Number.parseFloat(form.amount),
      currency: form.currency,
      frequency: form.frequency,
      due_day: Number.parseInt(form.due_day, 10),
      applies_to_level: form.applies_to_level || undefined,
    };

    try {
      if (editingId) {
        await updateFeeStructureMutation.mutateAsync({
          feeStructureId: editingId,
          payload,
        });
      } else {
        await createFeeStructureMutation.mutateAsync(payload);
      }
      setShowForm(false);
      setForm(EMPTY_FEE_FORM);
      setEditingId(null);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : t('app.error'));
    }
  }

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
          {t('billing.feeStructures.title')}
        </h1>
        <button className="btn btn-primary" onClick={openCreate}>
          + {t('billing.feeStructures.create')}
        </button>
      </div>

      <ErrorBanner
        error={error || (feeStructuresQuery.error instanceof Error ? feeStructuresQuery.error.message : null)}
        onDismiss={() => setError(null)}
        onRetry={() => void feeStructuresQuery.refetch()}
      />

      {items.length === 0 ? (
        <EmptyState message={t('billing.feeStructures.empty')} icon="💳" />
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('billing.feeStructures.name')}</th>
                <th>{t('billing.feeStructures.amount')}</th>
                <th>{t('billing.feeStructures.frequency')}</th>
                <th>{t('billing.feeStructures.level')}</th>
                <th>{t('billing.feeStructures.status')}</th>
                <th>{t('app.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.name}</td>
                  <td>{formatCurrency(item.amount, item.currency)}</td>
                  <td>{t(`billing.frequencies.${item.frequency}`, item.frequency)}</td>
                  <td>{item.applies_to_level || '—'}</td>
                  <td>{item.status}</td>
                  <td>
                    <button className="btn btn-sm btn-secondary" onClick={() => openEdit(item)}>
                      {t('billing.feeStructures.edit')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm ? (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>
              {editingId ? t('billing.feeStructures.edit') : t('billing.feeStructures.create')}
            </h2>
            <div className="form-field">
              <label>{t('billing.feeStructures.name')}</label>
              <input
                type="text"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeStructures.amount')}</label>
                <input
                  type="number"
                  step="0.01"
                  value={form.amount}
                  onChange={(event) => setForm({ ...form, amount: event.target.value })}
                />
              </div>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeStructures.currency')}</label>
                <select
                  className="filter-select"
                  value={form.currency}
                  onChange={(event) => setForm({ ...form, currency: event.target.value })}
                >
                  <option value="MAD">MAD</option>
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeStructures.frequency')}</label>
                <select
                  className="filter-select"
                  value={form.frequency}
                  onChange={(event) => setForm({ ...form, frequency: event.target.value })}
                >
                  <option value="monthly">{t('billing.frequencies.monthly')}</option>
                  <option value="trimester">{t('billing.frequencies.trimester')}</option>
                  <option value="annual">{t('billing.frequencies.annual')}</option>
                  <option value="one_time">{t('billing.frequencies.one_time')}</option>
                </select>
              </div>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeStructures.dueDay')}</label>
                <input
                  type="number"
                  min="1"
                  max="28"
                  value={form.due_day}
                  onChange={(event) => setForm({ ...form, due_day: event.target.value })}
                />
              </div>
            </div>
            <div className="form-field">
              <label>{t('billing.feeStructures.level')}</label>
              <input
                type="text"
                value={form.applies_to_level}
                onChange={(event) => setForm({ ...form, applies_to_level: event.target.value })}
                placeholder={t('billing.feeStructures.levelPlaceholder')}
              />
            </div>
            {!editingId ? (
              <div className="form-field">
                <label>{t('billing.feeStructures.academicYear')}</label>
                <input
                  type="text"
                  value={form.academic_year_id}
                  onChange={(event) => setForm({ ...form, academic_year_id: event.target.value })}
                  placeholder="UUID"
                />
              </div>
            ) : null}
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={saving || !form.name || !form.amount}
              >
                {saving ? t('app.loading') : t('app.save')}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
