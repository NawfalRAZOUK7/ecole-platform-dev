/**
 * Teacher Submissions — list, download files, inline grading.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /teacher/submissions and POST /submissions/{id}/grade.
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useGradeSubmission, useTeacherSubmissions } from '@/features/lms/teacher/model/useTeacher';
import type { SubmissionItem } from '@/features/lms/teacher/api/teacher.api';

export function SubmissionsPage() {
  const { t } = useTranslation();
  const [filterStatus, setFilterStatus] = useState('');
  const [gradingId, setGradingId] = useState<string | null>(null);
  const [gradeScore, setGradeScore] = useState('');
  const [gradeFeedback, setGradeFeedback] = useState('');
  const [gradePublish, setGradePublish] = useState(true);

  const submissionsQuery = useTeacherSubmissions({
    status: filterStatus || undefined,
  });
  const gradeSubmissionMutation = useGradeSubmission();

  const submissions: SubmissionItem[] = useMemo(
    () => submissionsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [submissionsQuery.data],
  );
  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(submissionsQuery.error ?? gradeSubmissionMutation.error, t('app.error')),
      [gradeSubmissionMutation.error, submissionsQuery.error, t],
    ),
  );

  function openGrading(submission: SubmissionItem) {
    setGradingId(submission.id);
    setGradeScore(submission.grade ? String(submission.grade.score) : '');
    setGradeFeedback(submission.grade?.feedback_text || '');
    setGradePublish(true);
  }

  async function handleGrade(event: FormEvent, submissionId: string) {
    event.preventDefault();
    await gradeSubmissionMutation.mutateAsync({
      submissionId,
      payload: {
        score: parseFloat(gradeScore),
        feedback_text: gradeFeedback.trim() || null,
        publish: gradePublish,
      },
    });
    await submissionsQuery.refetch();
    setGradingId(null);
    setGradeScore('');
    setGradeFeedback('');
  }

  if (submissionsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.submissions.title')}</h1>

      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="">{t('teacher.submissions.allStatuses')}</option>
          <option value="submitted">{t('teacher.submissions.statusSubmitted')}</option>
          <option value="graded">{t('teacher.submissions.statusGraded')}</option>
          <option value="draft">{t('teacher.submissions.statusDraft')}</option>
        </select>
      </div>

      {submissions.length === 0 ? (
        <EmptyState message={t('teacher.submissions.empty')} />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('teacher.submissions.student')}</th>
                  <th>{t('teacher.submissions.assignment')}</th>
                  <th>{t('teacher.submissions.status')}</th>
                  <th>{t('teacher.submissions.score')}</th>
                  <th>{t('teacher.submissions.submittedAt')}</th>
                  <th>{t('teacher.submissions.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((submission) => (
                  <tr key={submission.id}>
                    <td style={{ fontWeight: 600 }}>{submission.student_name}</td>
                    <td>{submission.assignment_title}</td>
                    <td>
                      <span className={`status-badge status-${submission.status}`}>
                        {submission.status}
                      </span>
                    </td>
                    <td>
                      {submission.grade
                        ? `${submission.grade.score}/${submission.assignment_total_points}`
                        : '—'}
                    </td>
                    <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {submission.submitted_at
                        ? new Date(submission.submitted_at).toLocaleString()
                        : '—'}
                    </td>
                    <td>
                      {(submission.status === 'submitted' || submission.status === 'graded') && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => openGrading(submission)}
                        >
                          {t('teacher.submissions.grade')}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {submissionsQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                className="btn btn-secondary"
                onClick={() => void submissionsQuery.fetchNextPage()}
                disabled={submissionsQuery.isFetchingNextPage}
              >
                {submissionsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}

      {gradingId && (
        <div className="card" style={{ marginTop: 20, maxWidth: 500 }}>
          <h3 style={{ marginBottom: 12, fontSize: 16, fontWeight: 600 }}>
            {t('teacher.submissions.gradeSubmission')}
          </h3>
          <form onSubmit={(event) => void handleGrade(event, gradingId)}>
            <div className="form-field" style={{ marginBottom: 12 }}>
              <label>{t('teacher.submissions.score')}</label>
              <input
                type="number"
                className="filter-input"
                value={gradeScore}
                onChange={(e) => setGradeScore(e.target.value)}
                required
                min="0"
                step="0.5"
                style={{ width: 120 }}
              />
            </div>
            <div className="form-field" style={{ marginBottom: 12 }}>
              <label>{t('teacher.submissions.feedback')}</label>
              <input
                className="filter-input"
                value={gradeFeedback}
                onChange={(e) => setGradeFeedback(e.target.value)}
                placeholder={t('teacher.submissions.feedbackPlaceholder')}
                style={{ width: '100%' }}
              />
            </div>
            <label className="checkbox-label" style={{ marginBottom: 12 }}>
              <input
                type="checkbox"
                checked={gradePublish}
                onChange={(e) => setGradePublish(e.target.checked)}
              />
              {t('teacher.submissions.publishGrade')}
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn btn-primary"
                type="submit"
                disabled={gradeSubmissionMutation.isPending}
              >
                {gradeSubmissionMutation.isPending ? t('app.loading') : t('app.save')}
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => setGradingId(null)}
              >
                {t('app.cancel')}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
