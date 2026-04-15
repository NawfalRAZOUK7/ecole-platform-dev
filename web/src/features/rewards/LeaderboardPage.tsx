import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { useRewardChildren, useRewardLeaderboard } from './useRewards';
import type { LeaderboardEntry } from './rewards.service';

interface PodiumCardProps {
  entry: LeaderboardEntry;
  highlight: boolean;
}

function PodiumCard({ entry, highlight }: PodiumCardProps) {
  const heights: Record<number, number> = {
    1: 160,
    2: 130,
    3: 110,
  };

  return (
    <article
      className="card"
      style={{
        padding: 20,
        display: 'grid',
        gap: 12,
        minHeight: heights[entry.rank] ?? 100,
        alignContent: 'end',
        border: highlight ? '2px solid var(--color-primary)' : undefined,
        background:
          entry.rank === 1
            ? 'linear-gradient(180deg, rgba(246,211,101,0.35) 0%, rgba(255,255,255,0) 100%)'
            : undefined,
      }}
    >
      <strong style={{ fontSize: 20 }}>#{entry.rank}</strong>
      <div>
        <div style={{ fontWeight: 700 }}>{entry.studentName}</div>
        <div style={{ color: 'var(--color-text-secondary)' }}>
          ⭐ {entry.stars} • Lv {entry.level}
        </div>
      </div>
    </article>
  );
}

export function LeaderboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { classId } = useParams<{ classId: string }>();
  const leaderboardQuery = useRewardLeaderboard(classId, 20, Boolean(classId));
  const childrenQuery = useRewardChildren(user?.role === 'PAR');

  const highlightedStudentIds = useMemo(() => {
    if (user?.role === 'STD' && user.id) {
      return new Set([user.id]);
    }

    if (user?.role === 'PAR') {
      return new Set((childrenQuery.data ?? []).map((child) => child.student_id));
    }

    return new Set<string>();
  }, [childrenQuery.data, user]);

  if (leaderboardQuery.isLoading) {
    return <LoadingState />;
  }

  if (!leaderboardQuery.data) {
    return (
      <div className="page">
        <div className="page-header page-header--split">
          <div>
            <h1 className="page-title">{t('rewards.leaderboard.title')}</h1>
            <p className="page-subtitle">{t('rewards.leaderboard.subtitle')}</p>
          </div>
        </div>
        <ErrorBanner
          error={
            leaderboardQuery.error instanceof Error
              ? leaderboardQuery.error.message
              : t('app.error')
          }
          onRetry={() => void leaderboardQuery.refetch()}
        />
        <EmptyState message={t('rewards.leaderboard.empty')} icon="🏆" />
      </div>
    );
  }

  const entries = leaderboardQuery.data;
  const podium = [2, 1, 3]
    .map((rank) => entries.find((entry) => entry.rank === rank))
    .filter((entry): entry is LeaderboardEntry => Boolean(entry));

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('rewards.leaderboard.title')}</h1>
          <p className="page-subtitle">{t('rewards.leaderboard.subtitle')}</p>
        </div>
      </div>

      <ErrorBanner
        error={leaderboardQuery.error instanceof Error ? leaderboardQuery.error.message : null}
        onRetry={() => void leaderboardQuery.refetch()}
      />

      {entries.length === 0 ? (
        <EmptyState message={t('rewards.leaderboard.empty')} icon="🏆" />
      ) : (
        <div style={{ display: 'grid', gap: 20 }}>
          {podium.length > 0 ? (
            <section>
              <h2 style={{ marginTop: 0 }}>{t('rewards.leaderboard.podium')}</h2>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: 16,
                  alignItems: 'end',
                }}
              >
                {podium.map((entry) => (
                  <PodiumCard
                    key={entry.studentId}
                    entry={entry}
                    highlight={highlightedStudentIds.has(entry.studentId)}
                  />
                ))}
              </div>
            </section>
          ) : null}

          <section className="card" style={{ padding: 20 }}>
            <div style={{ marginBottom: 16 }}>
              <h2 style={{ margin: 0 }}>{t('rewards.leaderboard.fullTable')}</h2>
            </div>

            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('rewards.leaderboard.rank')}</th>
                  <th>{t('rewards.leaderboard.student')}</th>
                  <th>{t('rewards.stats.stars')}</th>
                  <th>{t('rewards.stats.level')}</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => {
                  const highlight = highlightedStudentIds.has(entry.studentId);

                  return (
                    <tr
                      key={entry.studentId}
                      style={{
                        background: highlight ? 'rgba(68, 138, 255, 0.10)' : undefined,
                        fontWeight: highlight ? 700 : undefined,
                      }}
                    >
                      <td>#{entry.rank}</td>
                      <td>
                        {entry.studentName}
                        {highlight ? (
                          <span style={{ marginInlineStart: 8, color: 'var(--color-primary)' }}>
                            {t('rewards.leaderboard.you')}
                          </span>
                        ) : null}
                      </td>
                      <td>{entry.stars}</td>
                      <td>{entry.level}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>
        </div>
      )}
    </div>
  );
}
