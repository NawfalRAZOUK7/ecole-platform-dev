/**
 * Parent justification page — submit absence justification for a child.
 *
 * Reference: Phase 4C — Parent absence justification form
 * Calls POST /attendance/justifications with attendance_record_id + reason.
 */

import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';

type Step = 'form' | 'done';

export function ParentJustificationPage() {
  const { t } = useTranslation();
  const [step, setStep] = useState<Step>('form');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [attendanceRecordId, setAttendanceRecordId] = useState('');
  const [reason, setReason] = useState('');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!attendanceRecordId.trim() || !reason.trim()) return;
    setLoading(true);
    setError(null);

    try {
      await api.post('/attendance/justifications', {
        attendance_record_id: attendanceRecordId.trim(),
        reason: reason.trim(),
      });
      setStep('done');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setAttendanceRecordId('');
    setReason('');
    setStep('form');
    setError(null);
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('justification.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {step === 'done' && (
        <div className="card" style={{ maxWidth: 500 }}>
          <h3 style={{ color: 'var(--color-success)', marginBottom: 12, fontSize: 16, fontWeight: 600 }}>
            {t('justification.success')}
          </h3>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {t('justification.successMessage')}
          </p>
          <button className="btn btn-primary" onClick={handleReset}>
            {t('justification.submitAnother')}
          </button>
        </div>
      )}

      {step === 'form' && (
        <form onSubmit={handleSubmit}>
          <div className="card" style={{ maxWidth: 500 }}>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
              {t('justification.instructions')}
            </p>

            <div className="form-field" style={{ marginBottom: 16 }}>
              <label>{t('justification.attendanceRecordId')}</label>
              <input
                className="filter-input"
                value={attendanceRecordId}
                onChange={(e) => setAttendanceRecordId(e.target.value)}
                placeholder={t('justification.recordIdPlaceholder')}
                required
                disabled={loading}
                style={{ width: '100%' }}
              />
            </div>

            <div className="form-field" style={{ marginBottom: 16 }}>
              <label>{t('justification.reason')}</label>
              <textarea
                className="filter-input"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder={t('justification.reasonPlaceholder')}
                required
                disabled={loading}
                rows={4}
                maxLength={2000}
                style={{ width: '100%', resize: 'vertical' }}
              />
              <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                {reason.length}/2000
              </span>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !attendanceRecordId.trim() || !reason.trim()}
            >
              {loading ? t('app.loading') : t('justification.submit')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
