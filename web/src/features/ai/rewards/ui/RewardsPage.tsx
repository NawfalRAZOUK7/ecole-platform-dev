import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthContext';
import { useStudentClasses } from '@/features/lms/student/model/useStudent';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { RewardsOverview } from './RewardsOverview';
import {
  useMyRewards,
  useRewardBadges,
  useRewardChildren,
  useRewardClasses,
  useRewardClassStudents,
  useStudentRewardHistory,
} from '../model/useRewards';

function StudentRewardsHome() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const rewardsQuery = useMyRewards(Boolean(user?.id));
  const badgesQuery = useRewardBadges(Boolean(user?.id));
  const studentClassesQuery = useStudentClasses();
  const historyStudentId = rewardsQuery.data?.studentId ?? user?.id ?? null;
  const historyQuery = useStudentRewardHistory(historyStudentId, 10, Boolean(historyStudentId));

  if (rewardsQuery.isLoading || badgesQuery.isLoading || historyQuery.isLoading) {
    return <LoadingState />;
  }

  if (rewardsQuery.error || badgesQuery.error || historyQuery.error || !rewardsQuery.data) {
    return (
      <ErrorBanner
        error={
          rewardsQuery.error instanceof Error
            ? rewardsQuery.error.message
            : badgesQuery.error instanceof Error
              ? badgesQuery.error.message
              : historyQuery.error instanceof Error
                ? historyQuery.error.message
                : t('app.error')
        }
        onRetry={() => {
          void Promise.all([
            rewardsQuery.refetch(),
            badgesQuery.refetch(),
            historyQuery.refetch(),
            studentClassesQuery.refetch(),
          ]);
        }}
      />
    );
  }

  const firstClassId = studentClassesQuery.data?.[0]?.class_id ?? null;

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('rewards.title')}</h1>
          <p className="page-subtitle">{t('rewards.studentSubtitle')}</p>
        </div>
      </div>

      <RewardsOverview
        rewards={rewardsQuery.data}
        badges={badgesQuery.data ?? []}
        history={historyQuery.data ?? []}
        leaderboardHref={firstClassId ? `/classes/${firstClassId}/leaderboard` : null}
      />
    </div>
  );
}

function ParentRewardsHub() {
  const { t } = useTranslation();
  const childrenQuery = useRewardChildren(true);

  if (childrenQuery.isLoading) {
    return <LoadingState />;
  }

  if (childrenQuery.error) {
    return (
      <ErrorBanner
        error={childrenQuery.error instanceof Error ? childrenQuery.error.message : t('app.error')}
        onRetry={() => void childrenQuery.refetch()}
      />
    );
  }

  const children = childrenQuery.data ?? [];

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('rewards.parentTitle')}</h1>
          <p className="page-subtitle">{t('rewards.parentSubtitle')}</p>
        </div>
      </div>

      {children.length === 0 ? (
        <EmptyState message={t('rewards.noChildren')} icon="👨‍👩‍👧" />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 16,
          }}
        >
          {children.map((child) => (
            <Link
              key={child.student_id}
              className="card"
              to={`/students/${child.student_id}/rewards`}
              style={{
                padding: 20,
                display: 'grid',
                gap: 10,
                color: 'inherit',
                textDecoration: 'none',
              }}
            >
              <strong style={{ fontSize: 18 }}>{child.student_name}</strong>
              <span style={{ color: 'var(--color-text-secondary)' }}>
                {t('rewards.parentCardSubtitle')}
              </span>
              <span className="btn btn-secondary" style={{ justifySelf: 'start' }}>
                {t('rewards.viewRewards')}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function RewardsDirectory() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [selectedClassId, setSelectedClassId] = useState<string | null>(null);
  const classesQuery = useRewardClasses(true);
  const studentsQuery = useRewardClassStudents(selectedClassId, Boolean(selectedClassId));
  const classes = classesQuery.data ?? [];
  const students = studentsQuery.data ?? [];

  useEffect(() => {
    if (!selectedClassId && classes.length > 0) {
      setSelectedClassId(classes[0].id);
    }
  }, [classes, selectedClassId]);

  if (classesQuery.isLoading) {
    return <LoadingState />;
  }

  if (classesQuery.error || studentsQuery.error) {
    return (
      <ErrorBanner
        error={
          classesQuery.error instanceof Error
            ? classesQuery.error.message
            : studentsQuery.error instanceof Error
              ? studentsQuery.error.message
              : t('app.error')
        }
        onRetry={() => {
          void Promise.all([classesQuery.refetch(), studentsQuery.refetch()]);
        }}
      />
    );
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('rewards.directoryTitle')}</h1>
          <p className="page-subtitle">{t('rewards.directorySubtitle')}</p>
        </div>
      </div>

      {classes.length === 0 ? (
        <EmptyState message={t('rewards.directoryEmpty')} icon="🏫" />
      ) : (
        <div style={{ display: 'grid', gap: 20 }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: 16,
            }}
          >
            {classes.map((item) => (
              <article
                key={item.id}
                className="card"
                style={{
                  padding: 18,
                  display: 'grid',
                  gap: 12,
                  border:
                    selectedClassId === item.id ? '2px solid var(--color-primary)' : undefined,
                }}
              >
                <div>
                  <strong>{item.name}</strong>
                  <div style={{ color: 'var(--color-text-secondary)', marginTop: 4 }}>
                    {item.code}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setSelectedClassId(item.id)}
                  >
                    {t('rewards.viewStudents')}
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={() => navigate(`/classes/${item.id}/leaderboard`)}
                  >
                    {t('rewards.viewLeaderboard')}
                  </button>
                </div>
              </article>
            ))}
          </div>

          {selectedClassId ? (
            <section className="card" style={{ padding: 20 }}>
              <div style={{ marginBottom: 16 }}>
                <h2 style={{ margin: 0 }}>{t('rewards.classStudentsTitle')}</h2>
                <p style={{ margin: '6px 0 0', color: 'var(--color-text-secondary)' }}>
                  {t('rewards.classStudentsSubtitle')}
                </p>
              </div>

              {studentsQuery.isLoading ? (
                <LoadingState />
              ) : students.length === 0 ? (
                <EmptyState message={t('rewards.classStudentsEmpty')} icon="👥" />
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('rewards.leaderboard.student')}</th>
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
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => navigate(`/students/${student.id}/rewards`)}
                          >
                            {t('rewards.viewRewards')}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          ) : null}
        </div>
      )}
    </div>
  );
}

export function RewardsPage() {
  const { user } = useAuth();

  if (user?.role === 'STD') {
    return <StudentRewardsHome />;
  }

  if (user?.role === 'PAR') {
    return <ParentRewardsHub />;
  }

  return <RewardsDirectory />;
}
