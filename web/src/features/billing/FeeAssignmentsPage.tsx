/**
 * Fee Assignments page — assign fees to students/classes, apply discounts (ADM).
 *
 * Reference: Phase 12A — Billing Management
 * Calls GET/POST /billing/fee-assignments + POST /billing/fee-assignments/bulk.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';

interface FeeAssignment {
  id: string;
  fee_structure_id: string;
  student_id: string;
  school_id: string;
  discount_percent: number | null;
  discount_reason: string | null;
  status: string;
  created_at: string;
}

interface FeeStructure {
  id: string;
  name: string;
  amount: number;
  currency: string;
}

type AssignMode = 'individual' | 'bulk';

export function FeeAssignmentsPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<FeeAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feeStructures, setFeeStructures] = useState<FeeStructure[]>([]);

  // Assign form
  const [showForm, setShowForm] = useState(false);
  const [assignMode, setAssignMode] = useState<AssignMode>('individual');
  const [selectedFeeId, setSelectedFeeId] = useState('');
  const [studentId, setStudentId] = useState('');
  const [classId, setClassId] = useState('');
  const [level, setLevel] = useState('');
  const [discountPercent, setDiscountPercent] = useState('');
  const [discountReason, setDiscountReason] = useState('');
  const [saving, setSaving] = useState(false);
  const [bulkResult, setBulkResult] = useState<{ created: number; skipped: number } | null>(null);

  const fetchAssignments = useCallback(async () => {
    try {
      const resp = await api.list<FeeAssignment>('/billing/fee-assignments');
      setItems(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    Promise.all([
      fetchAssignments(),
      api.list<FeeStructure>('/billing/fee-structures').then((r) => setFeeStructures(r.data)),
    ]).finally(() => setLoading(false));
  }, [fetchAssignments]);

  async function handleAssign() {
    setSaving(true);
    setBulkResult(null);
    try {
      if (assignMode === 'individual') {
        await api.post('/billing/fee-assignments', {
          fee_structure_id: selectedFeeId,
          student_id: studentId,
          discount_percent: discountPercent ? parseFloat(discountPercent) : undefined,
          discount_reason: discountReason || undefined,
        });
      } else {
        const payload: Record<string, unknown> = {
          fee_structure_id: selectedFeeId,
          discount_percent: discountPercent ? parseFloat(discountPercent) : undefined,
          discount_reason: discountReason || undefined,
        };
        if (classId) payload.class_id = classId;
        if (level) payload.level = level;

        const resp = await api.post<{ created: number; skipped: number }>('/billing/fee-assignments/bulk', payload);
        setBulkResult(resp.data);
      }
      await fetchAssignments();
      if (assignMode === 'individual') {
        setShowForm(false);
        resetForm();
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSaving(false);
    }
  }

  function resetForm() {
    setSelectedFeeId('');
    setStudentId('');
    setClassId('');
    setLevel('');
    setDiscountPercent('');
    setDiscountReason('');
    setBulkResult(null);
  }

  function getFeeName(feeId: string): string {
    return feeStructures.find((f) => f.id === feeId)?.name || feeId.slice(0, 8);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('billing.feeAssignments.title')}</h1>
        <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(true); }}>
          + {t('billing.feeAssignments.assign')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchAssignments} />

      {items.length === 0 ? (
        <EmptyState message={t('billing.feeAssignments.empty')} icon="📋" />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('billing.feeAssignments.feeStructure')}</th>
                <th>{t('billing.feeAssignments.student')}</th>
                <th>{t('billing.feeAssignments.discount')}</th>
                <th>{t('billing.feeAssignments.status')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id}>
                  <td style={{ fontWeight: 600 }}>{getFeeName(a.fee_structure_id)}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{a.student_id.slice(0, 8)}...</td>
                  <td>
                    {a.discount_percent ? (
                      <span>{a.discount_percent}%{a.discount_reason ? ` (${a.discount_reason})` : ''}</span>
                    ) : '—'}
                  </td>
                  <td>
                    <span className="status-badge" style={{
                      color: a.status === 'ACTIVE' ? '#10b981' : a.status === 'EXEMPTED' ? '#f59e0b' : '#6b7280',
                      borderColor: a.status === 'ACTIVE' ? '#10b981' : a.status === 'EXEMPTED' ? '#f59e0b' : '#6b7280',
                    }}>
                      {t(`billing.statuses.${a.status}`, a.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Assign Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>{t('billing.feeAssignments.assign')}</h2>

            {/* Mode toggle */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              <button
                className={`btn btn-sm ${assignMode === 'individual' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setAssignMode('individual')}
              >
                {t('billing.feeAssignments.individual')}
              </button>
              <button
                className={`btn btn-sm ${assignMode === 'bulk' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setAssignMode('bulk')}
              >
                {t('billing.feeAssignments.bulk')}
              </button>
            </div>

            <div className="form-field">
              <label>{t('billing.feeAssignments.feeStructure')}</label>
              <select className="filter-select" value={selectedFeeId} onChange={(e) => setSelectedFeeId(e.target.value)}>
                <option value="">{t('billing.feeAssignments.selectFee')}</option>
                {feeStructures.map((f) => (
                  <option key={f.id} value={f.id}>{f.name} ({f.amount} {f.currency})</option>
                ))}
              </select>
            </div>

            {assignMode === 'individual' ? (
              <div className="form-field">
                <label>{t('billing.feeAssignments.studentId')}</label>
                <input type="text" value={studentId} onChange={(e) => setStudentId(e.target.value)} placeholder="UUID" />
              </div>
            ) : (
              <>
                <div className="form-field">
                  <label>{t('billing.feeAssignments.classId')}</label>
                  <input type="text" value={classId} onChange={(e) => setClassId(e.target.value)} placeholder={t('billing.feeAssignments.classIdPlaceholder')} />
                </div>
                <div className="form-field">
                  <label>{t('billing.feeAssignments.levelFilter')}</label>
                  <input type="text" value={level} onChange={(e) => setLevel(e.target.value)} placeholder={t('billing.feeAssignments.levelPlaceholder')} />
                </div>
              </>
            )}

            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeAssignments.discountPercent')}</label>
                <input type="number" min="0" max="100" value={discountPercent} onChange={(e) => setDiscountPercent(e.target.value)} placeholder="0" />
              </div>
              <div className="form-field" style={{ flex: 2 }}>
                <label>{t('billing.feeAssignments.discountReason')}</label>
                <input type="text" value={discountReason} onChange={(e) => setDiscountReason(e.target.value)} placeholder={t('billing.feeAssignments.discountReasonPlaceholder')} />
              </div>
            </div>

            {bulkResult && (
              <div style={{ padding: 12, background: '#ecfdf5', borderRadius: 8, marginTop: 12 }}>
                <strong>{t('billing.feeAssignments.bulkResult')}:</strong>{' '}
                {t('billing.feeAssignments.created')}: {bulkResult.created}, {t('billing.feeAssignments.skipped')}: {bulkResult.skipped}
              </div>
            )}

            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button className="btn btn-primary" onClick={handleAssign} disabled={saving || !selectedFeeId}>
                {saving ? t('app.loading') : t('billing.feeAssignments.assign')}
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
