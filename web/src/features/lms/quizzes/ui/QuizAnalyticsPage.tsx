import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { EmptyState, ErrorBanner, LoadingState, StatCard } from '@/shared/ui';
import { useQuizAnalytics } from '../model/useQuizzes';

function difficultyBucket(accuracy: number | null) {
  if (accuracy === null) return 'unanswered';
  if (accuracy < 40) return 'hard';
  if (accuracy < 75) return 'medium';
  return 'easy';
}

export function QuizAnalyticsPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const analyticsQuery = useQuizAnalytics(id);

  const questionStats = analyticsQuery.data?.question_stats ?? [];
  const completionRate = analyticsQuery.data?.total_attempts
    ? Math.round(
        (analyticsQuery.data.completed_attempts / analyticsQuery.data.total_attempts) * 100,
      )
    : 0;

  const scoreDistribution = useMemo(
    () => [
      {
        bucket: t('quizAnalytics.distribution.minimum'),
        score: analyticsQuery.data?.min_score_achieved ?? 0,
      },
      {
        bucket: t('quizAnalytics.distribution.average'),
        score: analyticsQuery.data?.average_score ?? 0,
      },
      {
        bucket: t('quizAnalytics.distribution.maximum'),
        score: analyticsQuery.data?.max_score_achieved ?? 0,
      },
    ],
    [
      analyticsQuery.data?.average_score,
      analyticsQuery.data?.max_score_achieved,
      analyticsQuery.data?.min_score_achieved,
      t,
    ],
  );

  const questionChart = useMemo(
    () =>
      questionStats.map((question, index) => ({
        label: `Q${index + 1}`,
        accuracy: question.accuracy ?? 0,
        attempts: question.total_responses,
        question: question.question_text,
      })),
    [questionStats],
  );

  const difficultyBreakdown = useMemo(() => {
    return questionStats.reduce<Record<string, number>>(
      (accumulator, question) => {
        const bucket = difficultyBucket(question.accuracy);
        accumulator[bucket] = (accumulator[bucket] || 0) + 1;
        return accumulator;
      },
      { easy: 0, medium: 0, hard: 0, unanswered: 0 },
    );
  }, [questionStats]);

  if (!id) {
    return null;
  }

  if (analyticsQuery.isLoading) {
    return <LoadingState />;
  }

  if (!analyticsQuery.data) {
    return <EmptyState message={t('quizAnalytics.empty')} />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{analyticsQuery.data.title}</h1>
        <p className="page-subtitle">{t('quizAnalytics.subtitle')}</p>
      </div>

      <ErrorBanner
        error={analyticsQuery.error instanceof Error ? analyticsQuery.error.message : null}
        onRetry={() => void analyticsQuery.refetch()}
      />

      <div className="gradebook-page__stats">
        <StatCard label="quizAnalytics.totalAttempts" value={analyticsQuery.data.total_attempts} />
        <StatCard
          label="quizAnalytics.completedAttempts"
          value={analyticsQuery.data.completed_attempts}
        />
        <StatCard label="quizAnalytics.completionRate" value={`${completionRate}%`} />
        <StatCard
          label="quizAnalytics.averageScore"
          value={
            analyticsQuery.data.average_percentage !== null
              ? `${analyticsQuery.data.average_percentage}%`
              : '—'
          }
        />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 16,
        }}
      >
        <section className="card" style={{ padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>{t('quizAnalytics.scoreDistribution')}</h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
            {t('quizAnalytics.scoreDistributionHint')}
          </p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={scoreDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="bucket" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="score" fill="var(--color-primary)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="card" style={{ padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>{t('quizAnalytics.difficultyBreakdown')}</h2>
          <div style={{ display: 'grid', gap: 10 }}>
            {(['easy', 'medium', 'hard', 'unanswered'] as const).map((bucket) => (
              <div
                key={bucket}
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              >
                <span>{t(`quizAnalytics.buckets.${bucket}`)}</span>
                <strong>{difficultyBreakdown[bucket] || 0}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="card" style={{ padding: 16, marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>{t('quizAnalytics.questionBreakdown')}</h2>
        {questionChart.length === 0 ? (
          <EmptyState message={t('quizAnalytics.noQuestions')} />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={questionChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="label" />
              <YAxis domain={[0, 100]} />
              <Tooltip
                formatter={(value: number) => `${value}%`}
                labelFormatter={(_label, payload) => payload?.[0]?.payload?.question || ''}
              />
              <Bar dataKey="accuracy" fill="var(--color-accent)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>
    </div>
  );
}
