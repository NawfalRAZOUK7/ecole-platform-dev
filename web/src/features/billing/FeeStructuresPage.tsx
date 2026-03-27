/**
 * Fee Structures management page — CRUD for fee structures (ADM only).
 *
 * Reference: Phase 12A — Billing Management
 * Calls GET/POST/PUT /billing/fee-structures.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatCurrency } from '@/shared/i18n';

interface FeeStructure {
  id: string;
  school_id: string;
  academic_year_id: string;
  name: string;
  amount: number;
  currency: string;
  frequency: string;
  due_day: number;
  applies_to_level: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

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
  const [items, setItems] = useState<FeeStructure[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FeeForm>(EMPTY_FEE_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchFees = useCallback(async () => {
    try {
      const resp = await api.list<FeeStructure>('/billing/fee-structures');
      setItems(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchFees().finally(() => setLoading(false));
  }, [fetchFees]);

  async function handleSave() {
    setSaving(true);
    try {
      const payload = {
        name: form.name,
        amount: parseFloat(form.amount),
        currency: form.currency,
        frequency: form.frequency,
        due_day: parseInt(form.due_day, 10),
        applies_to_level: form.applies_to_level || undefined,
        ...(editingId ? {} : { academic_year_id: form.academic_year_id || undefined }),
        ...(editingId ? { status: undefined } : {}),
      };

      if (editingId) {
        await api.put(`/billing/fee-structures/${editingId}`, payload);
      } else {
        await api.post('/billing/fee-structures', payload);
      }
      setShowForm(false);
      setForm(EMPTY_FEE_FORM);
      setEditingId(null);
      await fetchFees();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSaving(false);
    }
  }

  function openEdit(fee: FeeStructure) {
    setForm({
      academic_year_id: fee.academic_year_id,
      name: fee.name,
      amount: String(fee.amount),
      currency: fee.currency,
      frequency: fee.frequency,
      due_day: String(fee.due_day),
      applies_to_level: fee.applies_to_level || '',
    });
    setEditingId(fee.id);
    setShowForm(true);
  }

  function getStatusColor(status: string): string {
    return status === 'ACTIVE' ? '#10b981' : '#6b7280';
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('billing.feeStructures.title')}</h1>
        <button
          className="btn btn-primary"
          onClick={() => {
            setForm(EMPTY_FEE_FORM);
            setEditingId(null);
            setShowForm(true);
          }}
        >
          + {t('billing.feeStructures.create')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchFees} />

      {items.length === 0 ? (
        <EmptyState message={t('billing.feeStructures.empty')} icon="💰" />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('billing.feeStructures.name')}</th>
                <th>{t('billing.feeStructures.amount')}</th>
                <th>{t('billing.feeStructures.frequency')}</th>
                <th>{t('billing.feeStructures.dueDay')}</th>
                <th>{t('billing.feeStructures.level')}</th>
                <th>{t('billing.feeStructures.status')}</th>
                <th>{t('billing.feeStructures.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((fee) => (
                <tr key={fee.id}>
                  <td style={{ fontWeight: 600 }}>{fee.name}</td>
                  <td>{formatCurrency(fee.amount, fee.currency)}</td>
                  <td>{t(`billing.frequencies.${fee.frequency}`, fee.frequency)}</td>
                  <td>{fee.due_day}</td>
                  <td>{fee.applies_to_level || '—'}</td>
                  <td>
                    <span className="status-badge" style={{ color: getStatusColor(fee.status), borderColor: getStatusColor(fee.status) }}>
                      {t(`billing.statuses.${fee.status}`, fee.status)}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-sm btn-secondary" onClick={() => openEdit(fee)}>
                      ✏️ {t('billing.feeStructures.edit')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>
              {editingId ? t('billing.feeStructures.edit') : t('billing.feeStructures.create')}
            </h2>
            <div className="form-field">
              <label>{t('billing.feeStructures.name')}</label>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeStructures.amount')}</label>
                <input type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
              </div>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeStructures.currency')}</label>
                <select className="filter-select" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })}>
                  <option value="MAD">MAD</option>
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeStructures.frequency')}</label>
                <select className="filter-select" value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })}>
                  <option value="monthly">{t('billing.frequencies.monthly')}</option>
                  <option value="trimester">{t('billing.frequencies.trimester')}</option>
                  <option value="annual">{t('billing.frequencies.annual')}</option>
                  <option value="one_time">{t('billing.frequencies.one_time')}</option>
                </select>
              </div>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeStructures.dueDay')}</label>
                <input type="number" min="1" max="28" value={form.due_day} onChange={(e) => setForm({ ...form, due_day: e.target.value })} />
              </div>
            </div>
            <div className="form-field">
              <label>{t('billing.feeStructures.level')}</label>
              <input type="text" value={form.applies_to_level} onChange={(e) => setForm({ ...form, applies_to_level: e.target.value })} placeholder={t('billing.feeStructures.levelPlaceholder')} />
            </div>
            {!editingId && (
              <div className="form-field">
                <label>{t('billing.feeStructures.academicYear')}</label>
                <input type="text" value={form.academic_year_id} onChange={(e) => setForm({ ...form, academic_year_id: e.target.value })} placeholder="UUID" />
              </div>
            )}
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving || !form.name || !form.amount}>
                {saving ? t('app.loading') : t('app.save')}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
