/**
 * Teacher Assessment Form — create and publish assessments.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /assessments, POST /assessments, POST /assessments/{id}/publish.
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useCreateAssessment, usePublishAssessment, useTeacherAssessments, useTeacherClasses } from './useTeacher';
import type { AssessmentItem } from './teacher.service';

export function AssessmentFormPage() {
  const { t } = useTranslation();
  const [showForm, setShowForm] = useState(false);
  const [formClassId, setFormClassId] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formDueAt, setFormDueAt] = useState('');
  const [formWindowEnd, setFormWindowEnd] = useState('');
  const [formPoints, setFormPoints] = useState('20');
  const [filterClassId, setFilterClassId] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const classesQuery = useTeacherClasses();
  const assessmentsQuery = useTeacherAssessments({
    class_id: filterClassId || undefined,
    status: filterStatus || undefined,
  });
  const createAssessmentMutation = useCreateAssessment();
  const publishAssessmentMutation = usePublishAssessment();

  const classes = classesQuery.data ?? [];
  const assessments: AssessmentItem[] = useMemo(
    () => assessmentsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [assessmentsQuery.data]
  );
  const classMap = useMemo(
    () => Object.fromEntries(classes.map((item) => [item.id, `${item.code} — ${item.name}`])),
    [classes]
  );
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          classesQuery.error ?? assessmentsQuery.error ?? createAssessmentMutation.error ?? publishAssessmentMutation.error,
          t('app.error')
        ),
      [assessmentsQuery.error, classesQuery.error, createAssessmentMutation.error, publishAssessmentMutation.error, t]
    )
  );

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!formClassId || !formTitle.trim()) return;
    await createAssessmentMutation.mutateAsync({
      class_id: formClassId,
      title: formTitle.trim(),
      due_at: formDueAt ? new Date(formDueAt).toISOString() : null,
      window_end: formWindowEnd ? new Date(formWindowEnd).toISOString() : null,
      total_points: parseInt(formPoints, 10) || 0,
      status: 'draft',
    });
    await assessmentsQuery.refetch();
    setShowForm(false);
    setFormTitle('');
    setFormDueAt('');
    setFormWindowEnd('');
    setFormPoints('20');
  }

  async function handlePublish(assessmentId: string) {
    await publishAssessmentMutation.mutateAsync(assessmentId);
    await assessmentsQuery.refetch();
  }

  if (classesQuery.isLoading || assessmentsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.assessments.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void Promise.all([classesQuery.refetch(), assessmentsQuery.refetch()])}
      />

      <div className="filters-bar">
        <select className="filter-select" value={filterClassId} onChange={(e) => setFilterClassId(e.target.value)}>
          <option value="">{t('teacher.assessments.allClasses')}</option>
          {classes.map((item) => (
            <option key={item.id} value={item.id}>{item.code} — {item.name}</option>
          ))}
        </select>
        <select className="filter-select" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">{t('teacher.assessments.allStatuses')}</option>
          <option value="draft">{t('teacher.assessments.statusDraft')}</option>
          <option value="published">{t('teacher.assessments.statusPublished')}</option>
          <option value="closed">{t('teacher.assessments.statusClosed')}</option>
        </select>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? t('app.cancel') : t('teacher.assessments.create')}
        </button>
      </div>

      {showForm && (
        <form className="card" style={{ marginBottom: 20, maxWidth: 500 }} onSubmit={handleCreate}>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.class')}</label>
            <select className="filter-select" value={formClassId} onChange={(e) => setFormClassId(e.target.value)} required>
              <option value="">{t('teacher.assessments.selectClass')}</option>
              {classes.map((item) => (
                <option key={item.id} value={item.id}>{item.code} — {item.name}</option>
              ))}
            </select>
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.assessmentTitle')}</label>
            <input className="filter-input" value={formTitle} onChange={(e) => setFormTitle(e.target.value)} required style={{ width: '100%' }} />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.dueAt')}</label>
            <input type="datetime-local" className="filter-input" value={formDueAt} onChange={(e) => setFormDueAt(e.target.value)} style={{ width: '100%' }} />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.windowEnd')}</label>
            <input type="datetime-local" className="filter-input" value={formWindowEnd} onChange={(e) => setFormWindowEnd(e.target.value)} style={{ width: '100%' }} />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assessments.totalPoints')}</label>
            <input type="number" className="filter-input" value={formPoints} onChange={(e) => setFormPoints(e.target.value)} min="0" style={{ width: 120 }} />
          </div>
          <button className="btn btn-primary" type="submit" disabled={createAssessmentMutation.isPending}>
            {createAssessmentMutation.isPending ? t('app.loading') : t('teacher.assessments.create')}
          </button>
        </form>
      )}

      {assessments.length === 0 ? (
        <EmptyState message={t('teacher.assessments.empty')} />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('teacher.assessments.assessmentTitle')}</th>
                  <th>{t('teacher.assessments.class')}</th>
                  <th>{t('teacher.assessments.totalPoints')}</th>
                  <th>{t('teacher.assessments.status')}</th>
                  <th>{t('teacher.assessments.dueAt')}</th>
                  <th>{t('teacher.submissions.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {assessments.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontWeight: 600 }}>{item.title}</td>
                    <td>{classMap[item.class_id] || item.class_id.slice(0, 8)}</td>
                    <td>{item.total_points}</td>
                    <td><span className={`status-badge status-${item.status}`}>{item.status}</span></td>
                    <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {item.due_at ? new Date(item.due_at).toLocaleString() : '—'}
                    </td>
                    <td>
                      {item.status === 'draft' && (
                        <button className="btn btn-primary btn-sm" onClick={() => void handlePublish(item.id)}>
                          {t('teacher.assessments.publish')}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {assessmentsQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button className="btn btn-secondary" onClick={() => void assessmentsQuery.fetchNextPage()} disabled={assessmentsQuery.isFetchingNextPage}>
                {assessmentsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
