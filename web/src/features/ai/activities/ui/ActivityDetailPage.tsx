import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { formatDate } from '@/shared/i18n';
import { Badge, DataTable, ErrorBanner, LoadingState, StatCard, Tabs } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { ActivityParticipant, ActivitySession } from '../api/activities.api';
import {
  useActivityDetail,
  useCompleteActivitySession,
  useCreateActivitySession,
} from '../model/useActivities';

type SessionRow = ActivitySession & Record<string, unknown>;
type ParticipantRow = ActivityParticipant & Record<string, unknown>;
type ScoreBandRow = { label: string; count: number } & Record<string, unknown>;

function formatScore(score?: number | null) {
  if (score === null || score === undefined) {
    return '-';
  }

  return `${Math.round(score * 10) / 10}`;
}

function getParticipantRows(
  detailParticipants: ActivityParticipant[] | null | undefined,
  sessions: ActivitySession[],
) {
  if (detailParticipants?.length) {
    return detailParticipants;
  }

  const grouped = new Map<string, ActivityParticipant>();

  sessions.forEach((session) => {
    const current = grouped.get(session.student_id);
    if (!current) {
      grouped.set(session.student_id, {
        student_id: session.student_id,
        student_name: session.student_name || session.student_id,
        attempts: 1,
        completed_sessions: session.status === 'completed' ? 1 : 0,
        average_score: session.score ?? null,
        status: session.status,
        last_activity_at: session.completed_at || session.started_at || null,
      });
      return;
    }

    const totalAttempts = (current.attempts ?? 0) + 1;
    const completedSessions =
      (current.completed_sessions ?? 0) + (session.status === 'completed' ? 1 : 0);
    const scoreValues = [current.average_score, session.score].filter(
      (value): value is number => typeof value === 'number',
    );

    grouped.set(session.student_id, {
      ...current,
      attempts: totalAttempts,
      completed_sessions: completedSessions,
      average_score: scoreValues.length
        ? scoreValues.reduce((sum, value) => sum + value, 0) / scoreValues.length
        : null,
      status: session.status,
      last_activity_at:
        session.completed_at || session.started_at || current.last_activity_at || null,
    });
  });

  return Array.from(grouped.values());
}

export function ActivityDetailPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const detailQuery = useActivityDetail(id);
  const createSessionMutation = useCreateActivitySession();
  const completeSessionMutation = useCompleteActivitySession();
  const [score, setScore] = useState('80');
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const sessions = detailQuery.data?.sessions ?? [];
  const participants = useMemo(
    () => getParticipantRows(detailQuery.data?.participants, sessions),
    [detailQuery.data?.participants, sessions],
  );
  const activeSession = sessions.find((session) =>
    ['started', 'in_progress'].includes(session.status),
  );
  const gradingSummary = detailQuery.data?.grading;
  const scoreBands = gradingSummary?.score_bands ?? [];

  const sessionColumns: ColumnDef<SessionRow>[] = useMemo(
    () => [
      {
        key: 'attempt_no',
        header: 'activities.attempt',
      },
      {
        key: 'status',
        header: 'activities.status',
        render: (value) => (
          <Badge variant={String(value) === 'completed' ? 'success' : 'warning'}>
            {t(`activities.sessionStatus.${String(value)}`, {
              defaultValue: String(value),
            })}
          </Badge>
        ),
      },
      {
        key: 'score',
        header: 'activities.score',
        render: (value) => formatScore(typeof value === 'number' ? value : null),
      },
      {
        key: 'started_at',
        header: 'activities.startedAt',
        render: (value) => formatDate(String(value || ''), i18n.language),
      },
      {
        key: 'completed_at',
        header: 'activities.completedAt',
        render: (value) => formatDate(String(value || ''), i18n.language),
      },
    ],
    [i18n.language, t],
  );

  const participantColumns: ColumnDef<ParticipantRow>[] = useMemo(
    () => [
      {
        key: 'student_name',
        header: 'activities.student',
      },
      {
        key: 'attempts',
        header: 'activities.attempts',
      },
      {
        key: 'completed_sessions',
        header: 'activities.completedSessions',
      },
      {
        key: 'average_score',
        header: 'activities.averageScore',
        render: (value) => formatScore(typeof value === 'number' ? value : null),
      },
      {
        key: 'last_activity_at',
        header: 'activities.lastActivity',
        render: (value) => formatDate(String(value || ''), i18n.language),
      },
    ],
    [i18n.language],
  );

  const gradingColumns: ColumnDef<ScoreBandRow>[] = useMemo(
    () => [
      {
        key: 'label',
        header: 'activities.scoreRange',
      },
      {
        key: 'count',
        header: 'activities.studentsCount',
      },
    ],
    [],
  );

  async function handleStartSession() {
    if (!id) {
      return;
    }

    setFeedbackMessage(null);
    await createSessionMutation.mutateAsync({ activityId: id });
    setFeedbackMessage(t('activities.sessionStarted'));
  }

  async function handleCompleteSession() {
    if (!id || !activeSession) {
      return;
    }

    const parsedScore = Number(score);
    if (Number.isNaN(parsedScore)) {
      setFeedbackMessage(t('activities.invalidScore'));
      return;
    }

    setFeedbackMessage(null);
    await completeSessionMutation.mutateAsync({
      activityId: id,
      sessionId: activeSession.id,
      score: parsedScore,
    });
    setFeedbackMessage(t('activities.sessionCompleted'));
  }

  if (detailQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/activities')}
          >
            {t('activities.backToList')}
          </button>
          <h1 className="page-title">{detailQuery.data?.title ?? t('activities.title')}</h1>
          <p className="page-subtitle">
            {detailQuery.data?.objective ||
              detailQuery.data?.pedagogical_objective ||
              t('activities.noObjective')}
          </p>
        </div>
        <div className="page-actions">
          <Badge variant="info">
            {t(
              `activities.types.${detailQuery.data?.activity_type || detailQuery.data?.type || 'general'}`,
              {
                defaultValue:
                  detailQuery.data?.activity_type || detailQuery.data?.type || 'general',
              },
            )}
          </Badge>
          {detailQuery.data?.difficulty ? (
            <Badge variant="neutral">
              {t(`activities.difficultyValue.${detailQuery.data.difficulty}`, {
                defaultValue: detailQuery.data.difficulty,
              })}
            </Badge>
          ) : null}
          <button
            type="button"
            className="btn btn-primary"
            disabled={createSessionMutation.isPending}
            onClick={() => void handleStartSession()}
          >
            {createSessionMutation.isPending ? t('app.loading') : t('activities.startSession')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={toBannerError(
          detailQuery.error ?? createSessionMutation.error ?? completeSessionMutation.error,
          t('app.error'),
        )}
        onRetry={() => void detailQuery.refetch()}
      />

      {feedbackMessage ? (
        <div className="attendance-banner attendance-banner--success">{feedbackMessage}</div>
      ) : null}

      <div className="stats-grid">
        <StatCard label="activities.totalSessions" value={sessions.length} icon="🎮" />
        <StatCard label="activities.participants" value={participants.length} icon="👥" />
        <StatCard
          label="activities.averageScore"
          value={formatScore(gradingSummary?.average_score)}
          icon="📈"
        />
        <StatCard
          label="activities.completionRate"
          value={
            gradingSummary?.completion_rate
              ? `${Math.round(gradingSummary.completion_rate)}%`
              : '0%'
          }
          icon="✅"
        />
      </div>

      <div className="card">
        <h2>{t('activities.instructions')}</h2>
        <p>
          {detailQuery.data?.instructions ||
            detailQuery.data?.description ||
            t('activities.noInstructions')}
        </p>
      </div>

      <Tabs
        defaultTab="sessions"
        tabs={[
          {
            id: 'sessions',
            label: 'activities.sessions',
            content: (
              <DataTable
                columns={sessionColumns}
                data={sessions as SessionRow[]}
                loading={detailQuery.isFetching}
                emptyMessage="activities.noSessions"
                ariaLabel={t('activities.sessions')}
              />
            ),
          },
          {
            id: 'participants',
            label: 'activities.participation',
            content: (
              <DataTable
                columns={participantColumns}
                data={participants as ParticipantRow[]}
                loading={detailQuery.isFetching}
                emptyMessage="activities.noParticipants"
                ariaLabel={t('activities.participation')}
              />
            ),
          },
          {
            id: 'grading',
            label: 'activities.grading',
            content: (
              <div className="card-list">
                <div className="card">
                  <h3>{t('activities.gradeSession')}</h3>
                  <p>
                    {activeSession
                      ? t('activities.activeSessionFound')
                      : t('activities.noActiveSession')}
                  </p>
                  <div className="page-actions">
                    <input
                      type="number"
                      className="filter-input"
                      min="0"
                      max="100"
                      step="0.5"
                      value={score}
                      onChange={(event) => setScore(event.target.value)}
                      aria-label={t('activities.score')}
                    />
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={!activeSession || completeSessionMutation.isPending}
                      onClick={() => void handleCompleteSession()}
                    >
                      {completeSessionMutation.isPending
                        ? t('app.loading')
                        : t('activities.completeSession')}
                    </button>
                  </div>
                </div>
                <div className="card">
                  <DataTable
                    columns={gradingColumns}
                    data={scoreBands as ScoreBandRow[]}
                    loading={detailQuery.isFetching}
                    emptyMessage="activities.noGrades"
                    ariaLabel={t('activities.grading')}
                  />
                </div>
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}
