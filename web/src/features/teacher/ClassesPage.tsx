/**
 * Teacher Classes — assigned classes with student roster.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /teacher/classes and GET /teacher/classes/{id}/students.
 */

import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useTeacherClasses, useTeacherClassStudents } from './useTeacher';

export function ClassesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [selectedClassId, setSelectedClassId] = useState<string | null>(null);

  const classesQuery = useTeacherClasses();
  const studentsQuery = useTeacherClassStudents(selectedClassId);
  const classes = classesQuery.data ?? [];
  const students = studentsQuery.data ?? [];
  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(classesQuery.error ?? studentsQuery.error, t('app.error')),
      [classesQuery.error, studentsQuery.error, t],
    ),
  );

  function handleClassClick(classId: string) {
    setSelectedClassId((current) => (current === classId ? null : classId));
  }

  if (classesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.classes.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() =>
          void Promise.all([
            classesQuery.refetch(),
            selectedClassId ? studentsQuery.refetch() : Promise.resolve(null),
          ])
        }
      />

      {classes.length === 0 ? (
        <EmptyState message={t('teacher.classes.empty')} />
      ) : (
        <div className="teacher-classes-grid">
          {classes.map((item) => (
            <div key={item.id} className="teacher-class-card">
              <div className="teacher-class-header">
                <span className="teacher-class-code">{item.code}</span>
                <span className="teacher-class-name">{item.name}</span>
              </div>
              <div className="teacher-class-stats">
                <span>
                  {(item as { student_count?: number }).student_count ?? 0}{' '}
                  {t('teacher.classes.students')}
                </span>
                <span>
                  {(item as { course_count?: number }).course_count ?? 0}{' '}
                  {t('teacher.classes.courses')}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleClassClick(item.id)}
                >
                  {selectedClassId === item.id
                    ? t('teacher.classes.hideRoster')
                    : t('teacher.classes.viewRoster')}
                </button>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => navigate(`/classes/${item.id}/leaderboard`)}
                >
                  {t('teacher.classes.classLeaderboard')}
                </button>
              </div>

              {selectedClassId === item.id && (
                <div className="teacher-roster" style={{ marginTop: 12 }}>
                  {studentsQuery.isLoading ? (
                    <LoadingState />
                  ) : students.length === 0 ? (
                    <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      {t('teacher.classes.noStudents')}
                    </p>
                  ) : (
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>{t('teacher.classes.studentName')}</th>
                          <th>{t('teacher.classes.studentEmail')}</th>
                          <th>{t('teacher.classes.actions')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {students.map((student) => (
                          <tr key={student.id}>
                            <td>{student.full_name}</td>
                            <td>{student.email}</td>
                            <td>
                              <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => navigate(`/students/${student.id}/rewards`)}
                              >
                                {t('teacher.classes.viewRewards')}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
