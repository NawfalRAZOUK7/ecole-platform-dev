import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/shared/i18n';
import { Badge, EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { useQuizDetail, useQuizResults } from '../model/useQuizzes';
import type { QuizQuestion } from '../api/quizzes.api';

function formatAnswer(answer: unknown, question?: QuizQuestion) {
  if (answer === null || answer === undefined || answer === '') return '—';

  if (question?.question_type === 'MCQ' && Array.isArray(question.options)) {
    const choices = question.options as Array<{ id: string; text: string }>;
    const selected = Array.isArray(answer) ? answer : [answer];
    return selected
      .map((value) => choices.find((choice) => choice.id === value)?.text || String(value))
      .join(', ');
  }

  if (Array.isArray(answer)) return answer.join(', ');
  if (typeof answer === 'object')
    return Object.entries(answer as Record<string, unknown>)
      .map(([key, value]) => `${key}: ${String(value)}`)
      .join(', ');
  return String(answer);
}

function getDuration(startedAt: string, completedAt: string | null) {
  if (!completedAt) return '—';
  const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime();
  if (Number.isNaN(ms) || ms < 0) return '—';
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds}s`;
}

export function QuizResultsPage() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const resultsQuery = useQuizResults(id);
  const quizId = resultsQuery.data?.attempt.quiz_id;
  const quizQuery = useQuizDetail(quizId);

  const questionMap = useMemo(
    () => new Map((quizQuery.data?.questions ?? []).map((question) => [question.id, question])),
    [quizQuery.data?.questions],
  );

  if (!id) return null;
  if (resultsQuery.isLoading || (quizId && quizQuery.isLoading)) return <LoadingState />;
  if (!resultsQuery.data) return <EmptyState message={t('quizResults.empty')} />;

  const { attempt, responses } = resultsQuery.data;
  const percentage =
    attempt.max_score > 0 && attempt.score !== null
      ? Math.round((attempt.score / attempt.max_score) * 100)
      : null;

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{quizQuery.data?.title || t('quizResults.title')}</h1>
          <p className="page-subtitle">{t('quizResults.subtitle')}</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>
          {t('app.back')}
        </button>
      </div>

      <ErrorBanner
        error={
          resultsQuery.error instanceof Error
            ? resultsQuery.error.message
            : quizQuery.error instanceof Error
              ? quizQuery.error.message
              : null
        }
        onRetry={() =>
          void Promise.all([
            resultsQuery.refetch(),
            quizId ? quizQuery.refetch() : Promise.resolve(),
          ])
        }
      />

      <section className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: 16,
          }}
        >
          <div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {t('quizResults.scoreSummary')}
            </div>
            <strong style={{ fontSize: 28 }}>
              {attempt.score ?? 0}/{attempt.max_score}
            </strong>
          </div>
          <div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {t('quizResults.percentage')}
            </div>
            <strong style={{ fontSize: 28 }}>{percentage !== null ? `${percentage}%` : '—'}</strong>
          </div>
          <div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {t('quizResults.timeTaken')}
            </div>
            <strong>{getDuration(attempt.started_at, attempt.completed_at)}</strong>
          </div>
          <div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {t('quizResults.completedAt')}
            </div>
            <strong>
              {attempt.completed_at
                ? formatDate(attempt.completed_at, i18n.language, {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })
                : '—'}
            </strong>
          </div>
        </div>
      </section>

      {responses.length === 0 ? (
        <EmptyState message={t('quizResults.emptyResponses')} />
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {responses.map((response, index) => {
            const question = questionMap.get(response.question_id);
            const statusVariant =
              response.is_correct === null ? 'neutral' : response.is_correct ? 'success' : 'error';
            const statusLabel =
              response.is_correct === null
                ? t('quizResults.notGraded')
                : t(response.is_correct ? 'quizResults.correct' : 'quizResults.incorrect');

            return (
              <section
                key={response.question_id}
                className="card"
                style={{
                  padding: 16,
                  borderLeft: `4px solid var(${
                    response.is_correct === null
                      ? '--color-border'
                      : response.is_correct
                        ? '--color-success'
                        : '--color-error'
                  })`,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: 12,
                    alignItems: 'center',
                    marginBottom: 8,
                  }}
                >
                  <strong>{t('quizResults.questionLabel', { index: index + 1 })}</strong>
                  <Badge variant={statusVariant}>{statusLabel}</Badge>
                </div>
                <h3 style={{ marginTop: 0, fontSize: 16 }}>{response.question_text}</h3>
                <div style={{ fontSize: 14, marginBottom: 4 }}>
                  <strong>{t('quizResults.yourAnswer')}:</strong>{' '}
                  {formatAnswer(response.student_answer, question)}
                </div>
                <div style={{ fontSize: 14, marginBottom: 4 }}>
                  <strong>{t('quizResults.correctAnswer')}:</strong>{' '}
                  {formatAnswer(response.correct_answer, question)}
                </div>
                <div style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>
                  {t('quizResults.pointsLabel', {
                    earned: response.points_earned ?? 0,
                    total: response.points,
                  })}
                </div>
                {response.explanation ? (
                  <p
                    style={{ marginBottom: 0, marginTop: 10, color: 'var(--color-text-secondary)' }}
                  >
                    {response.explanation}
                  </p>
                ) : null}
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
