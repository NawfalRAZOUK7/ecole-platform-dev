import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { useSubmitJustification } from './useAttendance';

type Step = 'form' | 'done';

export function ParentJustificationPage() {
  const { t } = useTranslation();
  const submitJustificationMutation = useSubmitJustification();
  const [step, setStep] = useState<Step>('form');
  const [error, setError] = useState<string | null>(null);
  const [attendanceRecordId, setAttendanceRecordId] = useState('');
  const [reason, setReason] = useState('');

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!attendanceRecordId.trim() || !reason.trim()) {
      return;
    }

    setError(null);

    try {
      await submitJustificationMutation.mutateAsync({
        attendance_record_id: attendanceRecordId.trim(),
        reason: reason.trim(),
      });
      setStep('done');
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : t('app.error'));
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

      {step === 'done' ? (
        <div className="card" style={{ maxWidth: 500 }}>
          <h3
            style={{
              color: 'var(--color-success)',
              marginBottom: 12,
              fontSize: 16,
              fontWeight: 600,
            }}
          >
            {t('justification.success')}
          </h3>
          <p
            style={{
              fontSize: 14,
              color: 'var(--color-text-secondary)',
              marginBottom: 16,
            }}
          >
            {t('justification.successMessage')}
          </p>
          <button className="btn btn-primary" onClick={handleReset}>
            {t('justification.submitAnother')}
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="card" style={{ maxWidth: 500 }}>
            <p
              style={{
                fontSize: 13,
                color: 'var(--color-text-secondary)',
                marginBottom: 16,
              }}
            >
              {t('justification.instructions')}
            </p>

            <div className="form-field" style={{ marginBottom: 16 }}>
              <label>{t('justification.attendanceRecordId')}</label>
              <input
                className="filter-input"
                value={attendanceRecordId}
                onChange={(event) => setAttendanceRecordId(event.target.value)}
                placeholder={t('justification.recordIdPlaceholder')}
                required
                disabled={submitJustificationMutation.isPending}
                style={{ width: '100%' }}
              />
            </div>

            <div className="form-field" style={{ marginBottom: 16 }}>
              <label>{t('justification.reason')}</label>
              <textarea
                className="filter-input"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder={t('justification.reasonPlaceholder')}
                required
                disabled={submitJustificationMutation.isPending}
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
              disabled={
                submitJustificationMutation.isPending ||
                !attendanceRecordId.trim() ||
                !reason.trim()
              }
            >
              {submitJustificationMutation.isPending ? t('app.loading') : t('justification.submit')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
