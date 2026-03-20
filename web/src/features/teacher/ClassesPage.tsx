/**
 * Teacher Classes — assigned classes with student roster.
 *
 * Reference: Phase 4B — Teacher Dashboard
 * Calls GET /teacher/classes and GET /teacher/classes/{id}/students.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';

interface ClassItem {
  id: string;
  code: string;
  name: string;
  student_count: number;
  course_count: number;
}

interface StudentItem {
  id: string;
  full_name: string;
  email: string;
  enrollment_status: string;
}

export function ClassesPage() {
  const { t } = useTranslation();
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Student roster state
  const [selectedClassId, setSelectedClassId] = useState<string | null>(null);
  const [students, setStudents] = useState<StudentItem[]>([]);
  const [studentsLoading, setStudentsLoading] = useState(false);

  const fetchClasses = useCallback(async () => {
    try {
      const resp = await api.get<ClassItem[]>('/teacher/classes');
      setClasses(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchClasses().finally(() => setLoading(false));
  }, [fetchClasses]);

  const fetchStudents = useCallback(async (classId: string) => {
    setStudentsLoading(true);
    try {
      const resp = await api.get<StudentItem[]>(`/teacher/classes/${classId}/students`);
      setStudents(resp.data);
    } catch {
      setStudents([]);
    } finally {
      setStudentsLoading(false);
    }
  }, []);

  function handleClassClick(classId: string) {
    if (selectedClassId === classId) {
      setSelectedClassId(null);
      setStudents([]);
    } else {
      setSelectedClassId(classId);
      fetchStudents(classId);
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('teacher.classes.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchClasses} />

      {classes.length === 0 ? (
        <EmptyState message={t('teacher.classes.empty')} />
      ) : (
        <div className="teacher-classes-grid">
          {classes.map((cls) => (
            <div key={cls.id} className="teacher-class-card">
              <div className="teacher-class-header">
                <span className="teacher-class-code">{cls.code}</span>
                <span className="teacher-class-name">{cls.name}</span>
              </div>
              <div className="teacher-class-stats">
                <span>{cls.student_count} {t('teacher.classes.students')}</span>
                <span>{cls.course_count} {t('teacher.classes.courses')}</span>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handleClassClick(cls.id)}
              >
                {selectedClassId === cls.id
                  ? t('teacher.classes.hideRoster')
                  : t('teacher.classes.viewRoster')}
              </button>

              {selectedClassId === cls.id && (
                <div className="teacher-roster" style={{ marginTop: 12 }}>
                  {studentsLoading ? (
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
                        </tr>
                      </thead>
                      <tbody>
                        {students.map((s) => (
                          <tr key={s.id}>
                            <td>{s.full_name}</td>
                            <td>{s.email}</td>
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
