import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import {
  useBulkFeeAssignments,
  useCreateFeeAssignment,
  useFeeAssignments,
  useFeeStructures,
} from './useBilling';

type AssignMode = 'individual' | 'bulk';

export function FeeAssignmentsPage() {
  const { t } = useTranslation();
  const assignmentsQuery = useFeeAssignments();
  const feeStructuresQuery = useFeeStructures();
  const createAssignmentMutation = useCreateFeeAssignment();
  const bulkAssignmentsMutation = useBulkFeeAssignments();
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [assignMode, setAssignMode] = useState<AssignMode>('individual');
  const [selectedFeeId, setSelectedFeeId] = useState('');
  const [studentId, setStudentId] = useState('');
  const [classId, setClassId] = useState('');
  const [level, setLevel] = useState('');
  const [discountPercent, setDiscountPercent] = useState('');
  const [discountReason, setDiscountReason] = useState('');
  const [bulkResult, setBulkResult] = useState<{ created: number; skipped: number } | null>(null);

  if (assignmentsQuery.isLoading || feeStructuresQuery.isLoading) {
    return <LoadingState />;
  }

  const items = assignmentsQuery.data ?? [];
  const feeStructures = feeStructuresQuery.data ?? [];
  const saving = createAssignmentMutation.isPending || bulkAssignmentsMutation.isPending;

  async function handleAssign() {
    setError(null);
    setBulkResult(null);

    const discountValue = discountPercent ? Number.parseFloat(discountPercent) : undefined;
    const reasonValue = discountReason || undefined;

    try {
      if (assignMode === 'individual') {
        await createAssignmentMutation.mutateAsync({
          fee_structure_id: selectedFeeId,
          student_id: studentId,
          discount_percent: discountValue,
          discount_reason: reasonValue,
        });
      } else {
        const result = await bulkAssignmentsMutation.mutateAsync({
          fee_structure_id: selectedFeeId,
          class_id: classId || undefined,
          level: level || undefined,
          discount_percent: discountValue,
          discount_reason: reasonValue,
        });
        setBulkResult(result);
      }
      setShowForm(false);
      setStudentId('');
      setClassId('');
      setLevel('');
      setDiscountPercent('');
      setDiscountReason('');
    } catch (assignmentError) {
      setError(assignmentError instanceof Error ? assignmentError.message : t('app.error'));
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
          {t('billing.feeAssignments.title')}
        </h1>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + {t('billing.feeAssignments.assign')}
        </button>
      </div>

      <ErrorBanner
        error={
          error ||
          (assignmentsQuery.error instanceof Error ? assignmentsQuery.error.message : null) ||
          (feeStructuresQuery.error instanceof Error ? feeStructuresQuery.error.message : null)
        }
        onDismiss={() => setError(null)}
        onRetry={() => {
          void assignmentsQuery.refetch();
          void feeStructuresQuery.refetch();
        }}
      />

      {items.length === 0 ? (
        <EmptyState message={t('billing.feeAssignments.empty')} icon="🧾" />
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('billing.feeAssignments.feeStructure')}</th>
                <th>{t('billing.feeAssignments.studentId')}</th>
                <th>{t('billing.feeAssignments.discountPercent')}</th>
                <th>{t('billing.feeAssignments.discountReason')}</th>
                <th>{t('billing.feeAssignments.status')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.fee_structure_id}</td>
                  <td>{item.student_id}</td>
                  <td>{item.discount_percent ?? 0}%</td>
                  <td>{item.discount_reason || '—'}</td>
                  <td>{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm ? (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>{t('billing.feeAssignments.assign')}</h2>

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
              <select
                className="filter-select"
                value={selectedFeeId}
                onChange={(event) => setSelectedFeeId(event.target.value)}
              >
                <option value="">{t('billing.feeAssignments.selectFee')}</option>
                {feeStructures.map((feeStructure) => (
                  <option key={feeStructure.id} value={feeStructure.id}>
                    {feeStructure.name} ({feeStructure.amount} {feeStructure.currency})
                  </option>
                ))}
              </select>
            </div>

            {assignMode === 'individual' ? (
              <div className="form-field">
                <label>{t('billing.feeAssignments.studentId')}</label>
                <input
                  type="text"
                  value={studentId}
                  onChange={(event) => setStudentId(event.target.value)}
                  placeholder="UUID"
                />
              </div>
            ) : (
              <>
                <div className="form-field">
                  <label>{t('billing.feeAssignments.classId')}</label>
                  <input
                    type="text"
                    value={classId}
                    onChange={(event) => setClassId(event.target.value)}
                    placeholder={t('billing.feeAssignments.classIdPlaceholder')}
                  />
                </div>
                <div className="form-field">
                  <label>{t('billing.feeAssignments.levelFilter')}</label>
                  <input
                    type="text"
                    value={level}
                    onChange={(event) => setLevel(event.target.value)}
                    placeholder={t('billing.feeAssignments.levelPlaceholder')}
                  />
                </div>
              </>
            )}

            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-field" style={{ flex: 1 }}>
                <label>{t('billing.feeAssignments.discountPercent')}</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={discountPercent}
                  onChange={(event) => setDiscountPercent(event.target.value)}
                  placeholder="0"
                />
              </div>
              <div className="form-field" style={{ flex: 2 }}>
                <label>{t('billing.feeAssignments.discountReason')}</label>
                <input
                  type="text"
                  value={discountReason}
                  onChange={(event) => setDiscountReason(event.target.value)}
                  placeholder={t('billing.feeAssignments.discountReasonPlaceholder')}
                />
              </div>
            </div>

            {bulkResult ? (
              <div style={{ padding: 12, background: '#ecfdf5', borderRadius: 8, marginTop: 12 }}>
                <strong>{t('billing.feeAssignments.bulkResult')}:</strong>{' '}
                {t('billing.feeAssignments.created')}: {bulkResult.created},{' '}
                {t('billing.feeAssignments.skipped')}: {bulkResult.skipped}
              </div>
            ) : null}

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
      ) : null}
    </div>
  );
}
