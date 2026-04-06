/**
 * Student Quiz Player — take quizzes with all 5 question types,
 * timer, navigation, results with explanations.
 *
 * Phase 10B — Student Quiz Player (Web)
 * API: GET /quizzes, GET /quizzes/{id}, POST /quizzes/{id}/start,
 *      POST /attempts/{id}/respond, POST /attempts/{id}/submit,
 *      GET /attempts/{id}/results
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useAttemptResults,
  usePublishedQuizzes,
  useQuizDetail,
  useRespondToAttempt,
  useStartQuizAttempt,
  useSubmitAttempt,
} from './useStudent';
import type { Attempt, AttemptResult, Question, QuizListItem } from './student.service';

interface McqOptions {
  choices?: string[];
}

interface DragDropOptions {
  items?: string[];
  zones?: string[];
}

interface MatchingOptions {
  left?: string[];
  right?: string[];
}

type View = 'list' | 'playing' | 'results';

export function QuizPlayerPage() {
  const { t } = useTranslation();
  const [view, setView] = useState<View>('list');
  const [currentQuiz, setCurrentQuiz] = useState<QuizListItem | null>(null);
  const [selectedQuizId, setSelectedQuizId] = useState<string | null>(null);
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [resultAttemptId, setResultAttemptId] = useState<string | null>(null);
  const quizzesQuery = usePublishedQuizzes();
  const quizDetailQuery = useQuizDetail(selectedQuizId);
  const startAttemptMutation = useStartQuizAttempt();
  const respondMutation = useRespondToAttempt();
  const submitAttemptMutation = useSubmitAttempt();
  const resultsQuery = useAttemptResults(view === 'results' ? resultAttemptId : null);
  const quizzes = quizzesQuery.data ?? [];
  const questions: Question[] = quizDetailQuery.data?.questions ?? [];
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          quizzesQuery.error ??
            quizDetailQuery.error ??
            startAttemptMutation.error ??
            respondMutation.error ??
            submitAttemptMutation.error ??
            resultsQuery.error,
          t('app.error')
        ),
      [
        quizDetailQuery.error,
        quizzesQuery.error,
        respondMutation.error,
        resultsQuery.error,
        startAttemptMutation.error,
        submitAttemptMutation.error,
        t,
      ]
    )
  );

  async function handleStartQuiz(quiz: QuizListItem) {
    const startedAttempt = await startAttemptMutation.mutateAsync(quiz.id);
    setCurrentQuiz(quiz);
    setSelectedQuizId(quiz.id);
    setAttempt(startedAttempt);
    setCurrentIdx(0);
    setAnswers({});
    setResultAttemptId(null);
    setView('playing');
  }

  function handleSubmitAnswer(questionId: string, answer: unknown) {
    if (!attempt) {
      return;
    }
    setAnswers((current) => ({ ...current, [questionId]: answer }));
    void respondMutation.mutateAsync({
      attemptId: attempt.id,
      questionId,
      studentAnswer: answer,
    }).catch(() => null);
  }

  async function handleSubmitAttempt() {
    if (!attempt) {
      return;
    }

    for (const question of questions) {
      if (answers[question.id] !== undefined) {
        await respondMutation.mutateAsync({
          attemptId: attempt.id,
          questionId: question.id,
          studentAnswer: answers[question.id],
        }).catch(() => null);
      }
    }

    await submitAttemptMutation.mutateAsync(attempt.id);
    setResultAttemptId(attempt.id);
    setView('results');
  }

  function handleBackToList() {
    setView('list');
    setCurrentQuiz(null);
    setSelectedQuizId(null);
    setAttempt(null);
    setResultAttemptId(null);
    setAnswers({});
    void quizzesQuery.refetch();
  }

  if ((view === 'list' && quizzesQuery.isLoading) || (view === 'playing' && quizDetailQuery.isLoading) || (view === 'results' && resultsQuery.isLoading)) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('studentQuiz.title')}</h1>
      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void Promise.all([quizzesQuery.refetch(), selectedQuizId ? quizDetailQuery.refetch() : Promise.resolve(), resultAttemptId ? resultsQuery.refetch() : Promise.resolve()])}
      />

      {view === 'list' && <QuizList quizzes={quizzes} onStart={(quiz) => void handleStartQuiz(quiz)} />}

      {view === 'playing' && attempt && currentQuiz && (
        <QuizPlay
          quiz={currentQuiz}
          questions={questions}
          attempt={attempt}
          currentIdx={currentIdx}
          answers={answers}
          submitting={submitAttemptMutation.isPending}
          onNavigate={setCurrentIdx}
          onAnswer={handleSubmitAnswer}
          onSubmit={() => {
            void handleSubmitAttempt();
          }}
        />
      )}

      {view === 'results' && resultsQuery.data && <QuizResults results={resultsQuery.data} onBack={handleBackToList} />}
    </div>
  );
}

function QuizList({ quizzes, onStart }: { quizzes: QuizListItem[]; onStart: (quiz: QuizListItem) => void }) {
  const { t } = useTranslation();

  if (quizzes.length === 0) {
    return <EmptyState message={t('studentQuiz.empty')} />;
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
      {quizzes.map((quiz) => (
        <div key={quiz.id} className="card" style={{ padding: 16 }}>
          <h4 style={{ margin: '0 0 6px', fontSize: 15 }}>{quiz.title}</h4>
          {quiz.description && (
            <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0 0 8px' }}>
              {quiz.description.length > 100 ? `${quiz.description.slice(0, 100)}...` : quiz.description}
            </p>
          )}
          <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
            {quiz.subject && <span style={{ marginRight: 8 }}>{t(`cms.subjects.${quiz.subject}`, quiz.subject)}</span>}
            <span style={{ marginRight: 8 }}>{quiz.difficulty}</span>
            <span>{quiz.question_count} {t('studentQuiz.questions')}</span>
            {quiz.time_limit_minutes && <span style={{ marginLeft: 8 }}>{quiz.time_limit_minutes} min</span>}
          </div>
          <button className="btn btn-primary" onClick={() => onStart(quiz)}>
            {t('studentQuiz.startQuiz')}
          </button>
        </div>
      ))}
    </div>
  );
}

function QuizPlay({
  quiz,
  questions,
  attempt,
  currentIdx,
  answers,
  submitting,
  onNavigate,
  onAnswer,
  onSubmit,
}: {
  quiz: QuizListItem;
  questions: Question[];
  attempt: Attempt;
  currentIdx: number;
  answers: Record<string, unknown>;
  submitting: boolean;
  onNavigate: (idx: number) => void;
  onAnswer: (questionId: string, answer: unknown) => void;
  onSubmit: () => void;
}) {
  const { t } = useTranslation();
  const question = questions[currentIdx];
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (!quiz.time_limit_minutes || !attempt.started_at) {
      return;
    }
    const started = new Date(attempt.started_at).getTime();
    const endAt = started + quiz.time_limit_minutes * 60 * 1000;

    function tick() {
      const remaining = Math.max(0, Math.floor((endAt - Date.now()) / 1000));
      setTimeLeft(remaining);
      if (remaining <= 0) {
        clearInterval(timerRef.current);
        onSubmit();
      }
    }

    tick();
    timerRef.current = setInterval(tick, 1000);
    return () => clearInterval(timerRef.current);
  }, [attempt.started_at, onSubmit, quiz.time_limit_minutes]);

  function formatTime(seconds: number) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  if (!question) {
    return null;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <h3 style={{ margin: 0 }}>{quiz.title}</h3>
        {timeLeft !== null && (
          <span
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: timeLeft < 60 ? 'var(--color-error)' : 'var(--color-text)',
              fontFamily: 'monospace',
            }}
          >
            {formatTime(timeLeft)}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {questions.map((item, index) => (
          <button
            key={item.id}
            className={`btn ${index === currentIdx ? 'btn-primary' : answers[item.id] !== undefined ? 'btn-success' : 'btn-secondary'}`}
            style={{ width: 36, height: 36, padding: 0, fontSize: 13 }}
            onClick={() => onNavigate(index)}
          >
            {index + 1}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
          {t('studentQuiz.question')} {currentIdx + 1}/{questions.length} — {question.points} {t('studentQuiz.pts')}
        </div>
        <h4 style={{ margin: '0 0 16px', fontSize: 16 }}>{question.question_text}</h4>

        {question.question_type === 'mcq' && (
          <McqInput
            options={(question.options as McqOptions | null)?.choices || []}
            value={answers[question.id] as number | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}

        {question.question_type === 'true_false' && (
          <TrueFalseInput
            value={answers[question.id] as boolean | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}

        {question.question_type === 'fill_in_blank' && (
          <FillInInput
            value={answers[question.id] as string | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}

        {question.question_type === 'drag_drop' && (
          <DragDropInput
            options={question.options}
            value={answers[question.id] as Record<string, string> | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}

        {question.question_type === 'matching' && (
          <MatchingInput
            options={question.options}
            value={answers[question.id] as Record<string, string> | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button className="btn btn-secondary" disabled={currentIdx === 0} onClick={() => onNavigate(currentIdx - 1)}>
          {t('studentQuiz.prev')}
        </button>

        {currentIdx < questions.length - 1 ? (
          <button className="btn btn-primary" onClick={() => onNavigate(currentIdx + 1)}>
            {t('studentQuiz.next')}
          </button>
        ) : (
          <button className="btn btn-primary" onClick={onSubmit} disabled={submitting} style={{ background: 'var(--color-success)' }}>
            {submitting ? t('app.loading') : t('studentQuiz.submit')}
          </button>
        )}
      </div>
    </div>
  );
}

function McqInput({ options, value, onChange }: { options: string[]; value?: number; onChange: (value: number) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {options.map((option, index) => (
        <label
          key={index}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 12px',
            borderRadius: 'var(--radius)',
            background: value === index ? 'var(--color-surface-primary)' : 'var(--color-bg)',
            border: `1px solid ${value === index ? 'var(--color-primary)' : 'var(--color-border)'}`,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          <input type="radio" checked={value === index} onChange={() => onChange(index)} style={{ margin: 0 }} />
          <span style={{ fontSize: 14 }}>{option}</span>
        </label>
      ))}
    </div>
  );
}

function TrueFalseInput({ value, onChange }: { value?: boolean; onChange: (value: boolean) => void }) {
  const { t } = useTranslation();
  return (
    <div style={{ display: 'flex', gap: 16 }}>
      {[true, false].map((item) => (
        <label
          key={String(item)}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            padding: '14px 16px',
            borderRadius: 'var(--radius)',
            background: value === item ? 'var(--color-surface-primary)' : 'var(--color-bg)',
            border: `2px solid ${value === item ? 'var(--color-primary)' : 'var(--color-border)'}`,
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: 15,
            transition: 'all 0.2s',
          }}
        >
          <input type="radio" checked={value === item} onChange={() => onChange(item)} style={{ display: 'none' }} />
          {item ? t('studentQuiz.true') : t('studentQuiz.false')}
        </label>
      ))}
    </div>
  );
}

function FillInInput({ value, onChange }: { value?: string; onChange: (value: string) => void }) {
  const { t } = useTranslation();
  return (
    <input
      className="filter-input"
      value={value || ''}
      onChange={(event) => onChange(event.target.value)}
      placeholder={t('studentQuiz.typeAnswer')}
      style={{ width: '100%', fontSize: 15, padding: '10px 12px' }}
    />
  );
}

function DragDropInput({
  options,
  value,
  onChange,
}: {
  options: Record<string, unknown> | null;
  value?: Record<string, string>;
  onChange: (value: Record<string, string>) => void;
}) {
  const { t } = useTranslation();
  const items = (options as DragDropOptions | null)?.items || [];
  const zones = (options as DragDropOptions | null)?.zones || [];
  const current = value || {};

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8 }}>{t('studentQuiz.dragDropHint')}</p>
      {items.map((item, index) => (
        <div key={index} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 600, minWidth: 100 }}>{item}</span>
          <select
            className="filter-select"
            value={current[item] || ''}
            onChange={(event) => onChange({ ...current, [item]: event.target.value })}
            style={{ flex: 1 }}
          >
            <option value="">— {t('studentQuiz.selectZone')} —</option>
            {zones.map((zone) => (
              <option key={zone} value={zone}>{zone}</option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}

function MatchingInput({
  options,
  value,
  onChange,
}: {
  options: Record<string, unknown> | null;
  value?: Record<string, string>;
  onChange: (value: Record<string, string>) => void;
}) {
  const { t } = useTranslation();
  const left = (options as MatchingOptions | null)?.left || [];
  const right = (options as MatchingOptions | null)?.right || [];
  const current = value || {};

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8 }}>{t('studentQuiz.matchHint')}</p>
      {left.map((item, index) => (
        <div key={index} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 600, minWidth: 120 }}>{item}</span>
          <select
            className="filter-select"
            value={current[item] || ''}
            onChange={(event) => onChange({ ...current, [item]: event.target.value })}
            style={{ flex: 1 }}
          >
            <option value="">— {t('studentQuiz.selectMatch')} —</option>
            {right.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}

function QuizResults({ results, onBack }: { results: AttemptResult; onBack: () => void }) {
  const { t } = useTranslation();
  const { attempt, responses } = results;
  const pct = attempt.max_score && attempt.score !== null
    ? Math.round((attempt.score / attempt.max_score) * 100)
    : null;

  return (
    <div>
      <button className="btn btn-secondary" onClick={onBack} style={{ marginBottom: 16 }}>
        {t('studentQuiz.backToList')}
      </button>

      <div className="card" style={{ padding: 20, marginBottom: 16, textAlign: 'center' }}>
        <h2 style={{ margin: '0 0 8px' }}>{t('studentQuiz.resultsTitle')}</h2>
        <div style={{ fontSize: 40, fontWeight: 700, color: pct !== null && pct >= 50 ? 'var(--color-success)' : 'var(--color-error)' }}>
          {attempt.score !== null ? attempt.score : '—'} / {attempt.max_score}
        </div>
        {pct !== null && (
          <div style={{ fontSize: 16, color: 'var(--color-text-secondary)', marginTop: 4 }}>
            {pct}%
          </div>
        )}
      </div>

      {responses.map((response, index) => (
        <div
          key={response.question_id}
          className="card"
          style={{
            padding: 16,
            marginBottom: 12,
            borderLeft: `4px solid ${response.is_correct ? 'var(--color-success)' : 'var(--color-error)'}`,
          }}
        >
          <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 6 }}>
            {t('studentQuiz.question')} {index + 1} — {response.points_earned ?? 0}/{response.points}
          </div>
          <h4 style={{ margin: '0 0 8px', fontSize: 15 }}>{response.question_text}</h4>
          <div style={{ fontSize: 13, marginBottom: 4 }}>
            <strong>{t('studentQuiz.yourAnswer')}:</strong> {formatAnswer(response.student_answer)}
          </div>
          <div style={{ fontSize: 13, marginBottom: 4 }}>
            <strong>{t('studentQuiz.correctAnswer')}:</strong> {formatAnswer(response.correct_answer)}
          </div>
          {response.explanation && (
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 8, padding: 8, background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
              {response.explanation}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function formatAnswer(answer: unknown) {
  if (answer === null || answer === undefined || answer === '') {
    return '—';
  }
  if (typeof answer === 'string' || typeof answer === 'number' || typeof answer === 'boolean') {
    return String(answer);
  }
  return JSON.stringify(answer);
}
