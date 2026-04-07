import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/shared/ui/Badge';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import {
  useApplyGeneration,
  useGenerationJob,
  useGenerationPreview,
  useTimetableConstraints,
  useTriggerGeneration,
} from './useTimetable';
import type { GenerationJobStatus } from './timetable.service';

const DAY_LABELS: Record<number, string> = { 1: 'Lun', 2: 'Mar', 3: 'Mer', 4: 'Jeu', 5: 'Ven', 6: 'Sam' };

const STATUS_VARIANT: Record<GenerationJobStatus, 'info' | 'warning' | 'success' | 'error'> = {
  pending: 'info',
  running: 'warning',
  completed: 'success',
  failed: 'error',
};

export function TimetableGeneratePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const constraintsQuery = useTimetableConstraints();
  const triggerMutation = useTriggerGeneration();
  const applyMutation = useApplyGeneration();

  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmApply, setConfirmApply] = useState(false);
  const [applyResult, setApplyResult] = useState<{ applied: number; skipped: number } | null>(null);

  const academicYearId = constraintsQuery.data?.academic_year_id ?? '';

  const jobQuery = useGenerationJob(jobId ?? '', Boolean(jobId));
  const job = jobQuery.data;
  const isJobDone = job?.status === 'completed' || job?.status === 'failed';
  const isRunning = job?.status === 'pending' || job?.status === 'running';

  const previewQuery = useGenerationPreview(jobId ?? '', job?.status === 'completed');
  const preview = previewQuery.data;

  // Stop polling once done
  useEffect(() => {
    if (isJobDone) {
      void jobQuery.refetch();
    }
  }, [isJobDone, jobQuery]);

  async function handleTrigger() {
    if (!academicYearId) {
      setError(t('timetable.generate.noConstraints'));
      return;
    }
    setError(null);
    setApplyResult(null);
    setJobId(null);
    try {
      const newJob = await triggerMutation.mutateAsync(academicYearId);
      setJobId(newJob.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  async function handleApply() {
    if (!jobId) return;
    setError(null);
    try {
      const result = await applyMutation.mutateAsync(jobId);
      setApplyResult(result);
      setConfirmApply(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('timetable.generate.title')}</h1>
          <p className="page-subtitle">{t('timetable.generate.subtitle')}</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/timetable/constraints')}>
          {t('timetable.constraints.title')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {applyResult && (
        <div style={{ padding: '10px 16px', background: 'var(--color-success-bg, #f0fdf4)', border: '1px solid var(--color-success)', borderRadius: 8, marginBottom: 16, fontSize: 14, color: 'var(--color-success)' }}>
          {t('timetable.generate.applied', { applied: applyResult.applied, skipped: applyResult.skipped })}
        </div>
      )}

      {/* Trigger section */}
      <div className="card" style={{ padding: 24, marginBottom: 24, maxWidth: 520 }}>
        <h2 style={{ fontSize: 15, marginBottom: 8 }}>{t('timetable.generate.triggerTitle')}</h2>
        {constraintsQuery.isLoading ? (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>{t('app.loading')}</p>
        ) : academicYearId ? (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginBottom: 12 }}>
            {t('timetable.generate.academicYear')}: <strong>{academicYearId}</strong>
          </p>
        ) : (
          <p style={{ color: 'var(--color-warning)', fontSize: 13, marginBottom: 12 }}>
            {t('timetable.generate.noConstraints')}
          </p>
        )}
        <button
          type="button"
          className="btn btn-primary"
          disabled={triggerMutation.isPending || isRunning || !academicYearId}
          onClick={() => void handleTrigger()}
        >
          {triggerMutation.isPending || isRunning ? t('app.loading') : t('timetable.generate.trigger')}
        </button>
      </div>

      {/* Job status */}
      {job && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <span style={{ fontWeight: 600, fontSize: 14 }}>{t('timetable.generate.jobStatus')}</span>
            <Badge variant={STATUS_VARIANT[job.status]}>
              {t(`timetable.generate.statuses.${job.status}`)}
            </Badge>
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              {t('timetable.generate.jobId')}: {job.job_id}
            </span>
          </div>

          {/* Progress bar */}
          {isRunning && (
            <div style={{ height: 8, borderRadius: 4, background: 'var(--color-border)', maxWidth: 400, overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  borderRadius: 4,
                  background: 'var(--color-primary)',
                  width: `${job.progress}%`,
                  transition: 'width 0.4s ease',
                }}
              />
            </div>
          )}

          {job.status === 'failed' && job.error && (
            <p style={{ color: 'var(--color-danger)', fontSize: 13, marginTop: 6 }}>{job.error}</p>
          )}
        </div>
      )}

      {/* Preview */}
      {previewQuery.isLoading && <LoadingState />}

      {preview && preview.slots.length > 0 && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ fontSize: 15 }}>
              {t('timetable.generate.previewTitle', { count: preview.slots.length })}
            </h2>
            {!applyResult && (
              <button
                type="button"
                className="btn btn-primary"
                disabled={applyMutation.isPending}
                onClick={() => setConfirmApply(true)}
              >
                {t('timetable.generate.apply')}
              </button>
            )}
          </div>

          {preview.warnings.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              {preview.warnings.map((w, i) => (
                <div key={i} style={{ padding: '6px 12px', background: 'var(--color-warning-bg, #fffbeb)', border: '1px solid var(--color-warning)', borderRadius: 6, fontSize: 13, marginBottom: 4 }}>
                  ⚠️ {w}
                </div>
              ))}
            </div>
          )}

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('timetable.generate.cols.day')}</th>
                  <th>{t('timetable.generate.cols.time')}</th>
                  <th>{t('timetable.generate.cols.subject')}</th>
                  <th>{t('timetable.generate.cols.class')}</th>
                  <th>{t('timetable.generate.cols.teacher')}</th>
                  <th>{t('timetable.generate.cols.room')}</th>
                </tr>
              </thead>
              <tbody>
                {preview.slots.map((slot, i) => (
                  <tr key={i}>
                    <td>{DAY_LABELS[slot.day_of_week] ?? slot.day_of_week}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>{slot.start_time} – {slot.end_time}</td>
                    <td>{slot.subject}</td>
                    <td>{slot.class_id}</td>
                    <td>{slot.teacher_id}</td>
                    <td>{slot.room ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confirm apply dialog */}
      {confirmApply && (
        <div className="modal-overlay" onClick={() => setConfirmApply(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 400 }}>
            <h2 style={{ marginBottom: 12 }}>{t('timetable.generate.confirmApplyTitle')}</h2>
            <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 20 }}>
              {t('timetable.generate.confirmApplyBody')}
            </p>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setConfirmApply(false)}>{t('app.cancel')}</button>
              <button
                type="button"
                className="btn btn-primary"
                disabled={applyMutation.isPending}
                onClick={() => void handleApply()}
              >
                {applyMutation.isPending ? t('app.loading') : t('timetable.generate.applyConfirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
