/**
 * Teacher Assignment Form — create assignment for a course.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /courses, GET /assignments, POST /assignments.
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useCreateAssignment, useTeacherAssignments, useTeacherCourses } from './useTeacher';
import type { AssignmentItem, CourseItem } from './teacher.service';

export function AssignmentFormPage() {
  const { t } = useTranslation();
  const [showForm, setShowForm] = useState(false);
  const [formCourseId, setFormCourseId] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formDueAt, setFormDueAt] = useState('');
  const [formPoints, setFormPoints] = useState('20');
  const [filterCourseId, setFilterCourseId] = useState('');

  const coursesQuery = useTeacherCourses({});
  const assignmentsQuery = useTeacherAssignments({
    course_id: filterCourseId || undefined,
  });
  const createAssignmentMutation = useCreateAssignment();

  const courses: CourseItem[] = useMemo(
    () => coursesQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [coursesQuery.data]
  );
  const assignments: AssignmentItem[] = useMemo(
    () => assignmentsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [assignmentsQuery.data]
  );
  const courseMap = useMemo(
    () => Object.fromEntries(courses.map((item) => [item.id, item.title])),
    [courses]
  );
  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(coursesQuery.error ?? assignmentsQuery.error ?? createAssignmentMutation.error, t('app.error')),
      [assignmentsQuery.error, coursesQuery.error, createAssignmentMutation.error, t]
    )
  );

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!formCourseId || !formTitle.trim()) return;
    await createAssignmentMutation.mutateAsync({
      course_id: formCourseId,
      title: formTitle.trim(),
      description: formDesc.trim() || null,
      due_at: formDueAt ? new Date(formDueAt).toISOString() : null,
      total_points: parseInt(formPoints, 10) || 0,
    });
    await assignmentsQuery.refetch();
    setShowForm(false);
    setFormTitle('');
    setFormDesc('');
    setFormDueAt('');
    setFormPoints('20');
  }

  if (coursesQuery.isLoading || assignmentsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.assignments.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void Promise.all([coursesQuery.refetch(), assignmentsQuery.refetch()])}
      />

      <div className="filters-bar">
        <select className="filter-select" value={filterCourseId} onChange={(e) => setFilterCourseId(e.target.value)}>
          <option value="">{t('teacher.assignments.allCourses')}</option>
          {courses.map((item) => (
            <option key={item.id} value={item.id}>{item.title}</option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? t('app.cancel') : t('teacher.assignments.create')}
        </button>
      </div>

      {showForm && (
        <form className="card" style={{ marginBottom: 20, maxWidth: 500 }} onSubmit={handleCreate}>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.course')}</label>
            <select className="filter-select" value={formCourseId} onChange={(e) => setFormCourseId(e.target.value)} required>
              <option value="">{t('teacher.assignments.selectCourse')}</option>
              {courses.map((item) => (
                <option key={item.id} value={item.id}>{item.title}</option>
              ))}
            </select>
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.assignmentTitle')}</label>
            <input className="filter-input" value={formTitle} onChange={(e) => setFormTitle(e.target.value)} required style={{ width: '100%' }} />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.description')}</label>
            <input className="filter-input" value={formDesc} onChange={(e) => setFormDesc(e.target.value)} style={{ width: '100%' }} />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.dueAt')}</label>
            <input type="datetime-local" className="filter-input" value={formDueAt} onChange={(e) => setFormDueAt(e.target.value)} style={{ width: '100%' }} />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.assignments.totalPoints')}</label>
            <input type="number" className="filter-input" value={formPoints} onChange={(e) => setFormPoints(e.target.value)} min="0" style={{ width: 120 }} />
          </div>
          <button className="btn btn-primary" type="submit" disabled={createAssignmentMutation.isPending}>
            {createAssignmentMutation.isPending ? t('app.loading') : t('teacher.assignments.create')}
          </button>
        </form>
      )}

      {assignments.length === 0 ? (
        <EmptyState message={t('teacher.assignments.empty')} />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('teacher.assignments.assignmentTitle')}</th>
                  <th>{t('teacher.assignments.course')}</th>
                  <th>{t('teacher.assignments.totalPoints')}</th>
                  <th>{t('teacher.assignments.dueAt')}</th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontWeight: 600 }}>{item.title}</td>
                    <td>{courseMap[item.course_id] || item.course_id.slice(0, 8)}</td>
                    <td>{item.total_points}</td>
                    <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {item.due_at ? new Date(item.due_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {assignmentsQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button className="btn btn-secondary" onClick={() => void assignmentsQuery.fetchNextPage()} disabled={assignmentsQuery.isFetchingNextPage}>
                {assignmentsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
