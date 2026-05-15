/**
 * Teacher Courses — manage courses for assigned classes.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /courses and POST /courses.
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useCreateCourse,
  useTeacherClasses,
  useTeacherCourses,
} from '@/features/lms/teacher/model/useTeacher';
import type { CourseItem } from '@/features/lms/teacher/api/teacher.api';

export function CoursesPage() {
  const { t } = useTranslation();
  const [showForm, setShowForm] = useState(false);
  const [formClassId, setFormClassId] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formStatus, setFormStatus] = useState('draft');
  const [filterClassId, setFilterClassId] = useState('');

  const classesQuery = useTeacherClasses();
  const coursesQuery = useTeacherCourses({
    class_id: filterClassId || undefined,
  });
  const createCourseMutation = useCreateCourse();

  const classes = classesQuery.data ?? [];
  const courses: CourseItem[] = useMemo(
    () => coursesQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [coursesQuery.data],
  );
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          classesQuery.error ?? coursesQuery.error ?? createCourseMutation.error,
          t('app.error'),
        ),
      [classesQuery.error, coursesQuery.error, createCourseMutation.error, t],
    ),
  );
  const classMap = useMemo(
    () => Object.fromEntries(classes.map((item) => [item.id, `${item.code} — ${item.name}`])),
    [classes],
  );

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!formClassId || !formTitle.trim()) return;
    await createCourseMutation.mutateAsync({
      class_id: formClassId,
      title: formTitle.trim(),
      description: formDesc.trim() || null,
      status: formStatus,
    });
    await coursesQuery.refetch();
    setShowForm(false);
    setFormTitle('');
    setFormDesc('');
    setFormStatus('draft');
  }

  if (classesQuery.isLoading || coursesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.courses.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void Promise.all([classesQuery.refetch(), coursesQuery.refetch()])}
      />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={filterClassId}
          onChange={(e) => setFilterClassId(e.target.value)}
        >
          <option value="">{t('teacher.courses.allClasses')}</option>
          {classes.map((item) => (
            <option key={item.id} value={item.id}>
              {item.code} — {item.name}
            </option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? t('app.cancel') : t('teacher.courses.create')}
        </button>
      </div>

      {showForm && (
        <form className="card" style={{ marginBottom: 20, maxWidth: 500 }} onSubmit={handleCreate}>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.courses.class')}</label>
            <select
              className="filter-select"
              value={formClassId}
              onChange={(e) => setFormClassId(e.target.value)}
              required
            >
              <option value="">{t('teacher.courses.selectClass')}</option>
              {classes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.code} — {item.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.courses.courseTitle')}</label>
            <input
              className="filter-input"
              value={formTitle}
              onChange={(e) => setFormTitle(e.target.value)}
              required
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.courses.description')}</label>
            <input
              className="filter-input"
              value={formDesc}
              onChange={(e) => setFormDesc(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-field" style={{ marginBottom: 12 }}>
            <label>{t('teacher.courses.status')}</label>
            <select
              className="filter-select"
              value={formStatus}
              onChange={(e) => setFormStatus(e.target.value)}
            >
              <option value="draft">{t('teacher.courses.statusDraft')}</option>
              <option value="published">{t('teacher.courses.statusPublished')}</option>
            </select>
          </div>
          <button
            className="btn btn-primary"
            type="submit"
            disabled={createCourseMutation.isPending}
          >
            {createCourseMutation.isPending ? t('app.loading') : t('teacher.courses.create')}
          </button>
        </form>
      )}

      {courses.length === 0 ? (
        <EmptyState message={t('teacher.courses.empty')} />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('teacher.courses.courseTitle')}</th>
                  <th>{t('teacher.courses.class')}</th>
                  <th>{t('teacher.courses.status')}</th>
                  <th>{t('teacher.courses.description')}</th>
                </tr>
              </thead>
              <tbody>
                {courses.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontWeight: 600 }}>{item.title}</td>
                    <td>{classMap[item.class_id] || item.class_id.slice(0, 8)}</td>
                    <td>
                      <span className={`status-badge status-${item.status}`}>{item.status}</span>
                    </td>
                    <td style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
                      {item.description || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {coursesQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                className="btn btn-secondary"
                onClick={() => void coursesQuery.fetchNextPage()}
                disabled={coursesQuery.isFetchingNextPage}
              >
                {coursesQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
