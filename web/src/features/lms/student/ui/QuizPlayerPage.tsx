/**
 * Student Quiz Player — take quizzes with all 5 question types,
 * timer, navigation, results with explanations.
 *
 * Phase 10B — Student Quiz Player (Web)
 * API: GET /quizzes, GET /quizzes/{id}, POST /quizzes/{id}/start,
 *      POST /attempts/{id}/respond, POST /attempts/{id}/submit,
 *      GET /attempts/{id}/results
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  usePublishedQuizzes,
  useQuizDetail,
  useRespondToAttempt,
  useStartQuizAttempt,
  useSubmitAttempt,
} from '@/features/lms/student/model/useStudent';
import type { Attempt, Question, QuizListItem } from '@/features/lms/student/api/student.api';

interface ChoiceOption {
  id: string;
  text: string;
}

interface DragDropOptions {
  items?: ChoiceOption[];
  zones?: ChoiceOption[];
}

interface MatchingOptions {
  left?: ChoiceOption[];
  right?: ChoiceOption[];
}

type View = 'list' | 'playing';

export function QuizPlayerPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [view, setView] = useState<View>('list');
  const [currentQuiz, setCurrentQuiz] = useState<QuizListItem | null>(null);
  const [selectedQuizId, setSelectedQuizId] = useState<string | null>(null);
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const quizzesQuery = usePublishedQuizzes();
  const quizDetailQuery = useQuizDetail(selectedQuizId);
  const startAttemptMutation = useStartQuizAttempt();
  const respondMutation = useRespondToAttempt();
  const submitAttemptMutation = useSubmitAttempt();
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
            submitAttemptMutation.error,
          t('app.error'),
        ),
      [
        quizDetailQuery.error,
        quizzesQuery.error,
        respondMutation.error,
        startAttemptMutation.error,
        submitAttemptMutation.error,
        t,
      ],
    ),
  );

  async function handleStartQuiz(quiz: QuizListItem) {
    const startedAttempt = await startAttemptMutation.mutateAsync(quiz.id);
    setCurrentQuiz(quiz);
    setSelectedQuizId(quiz.id);
    setAttempt(startedAttempt);
    setCurrentIdx(0);
    setAnswers({});
    setView('playing');
  }

  function handleSubmitAnswer(questionId: string, answer: unknown) {
    if (!attempt) {
      return;
    }
    setAnswers((current) => ({ ...current, [questionId]: answer }));
    void respondMutation
      .mutateAsync({
        attemptId: attempt.id,
        questionId,
        studentAnswer: answer,
      })
      .catch(() => null);
  }

  const handleSubmitAttempt = useCallback(async () => {
    if (!attempt) {
      return;
    }

    await submitAttemptMutation.mutateAsync(attempt.id);
    navigate(`/quizzes/attempts/${attempt.id}/results`, { replace: true });
  }, [attempt, navigate, submitAttemptMutation]);

  if (
    (view === 'list' && quizzesQuery.isLoading) ||
    (view === 'playing' && quizDetailQuery.isLoading)
  ) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('studentQuiz.title')}</h1>
      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() =>
          void Promise.all([
            quizzesQuery.refetch(),
            selectedQuizId ? quizDetailQuery.refetch() : Promise.resolve(),
          ])
        }
      />

      {view === 'list' && (
        <QuizList quizzes={quizzes} onStart={(quiz) => void handleStartQuiz(quiz)} />
      )}

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
          onSubmit={handleSubmitAttempt}
        />
      )}
    </div>
  );
}

function QuizList({
  quizzes,
  onStart,
}: {
  quizzes: QuizListItem[];
  onStart: (quiz: QuizListItem) => void;
}) {
  const { t } = useTranslation();

  if (quizzes.length === 0) {
    return <EmptyState message={t('studentQuiz.empty')} />;
  }

  const recommended = quizzes.filter((q) => q.recommended);
  const others = quizzes.filter((q) => !q.recommended);
  const sorted = [...recommended, ...others];

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 16,
      }}
    >
      {sorted.map((quiz) => (
        <div
          key={quiz.id}
          className="card"
          style={{
            padding: 16,
            border: quiz.recommended ? '2px solid var(--color-primary)' : undefined,
          }}
        >
          {quiz.recommended && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                background: 'var(--color-surface-primary)',
                color: 'var(--color-primary)',
                fontSize: 11,
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: 999,
                marginBottom: 8,
              }}
            >
              ⭐ {t('studentQuiz.recommended', 'Recommandé pour toi')}
            </div>
          )}
          <h4 style={{ margin: '0 0 6px', fontSize: 15 }}>{quiz.title}</h4>
          {quiz.description && (
            <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0 0 8px' }}>
              {quiz.description.length > 100
                ? `${quiz.description.slice(0, 100)}...`
                : quiz.description}
            </p>
          )}
          <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
            {quiz.subject && (
              <span style={{ marginRight: 8 }}>
                {t(`cms.subjects.${quiz.subject}`, quiz.subject)}
              </span>
            )}
            <span style={{ marginRight: 8 }}>{quiz.difficulty}</span>
            <span>
              {quiz.question_count} {t('studentQuiz.questions')}
            </span>
            {quiz.time_limit_minutes && (
              <span style={{ marginLeft: 8 }}>{quiz.time_limit_minutes} min</span>
            )}
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
  onSubmit: () => void | Promise<void>;
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
        void onSubmit();
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
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
          flexWrap: 'wrap',
          gap: 8,
        }}
      >
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
          {t('studentQuiz.question')} {currentIdx + 1}/{questions.length} — {question.points}{' '}
          {t('studentQuiz.pts')}
        </div>
        <h4 style={{ margin: '0 0 16px', fontSize: 16 }}>{question.question_text}</h4>

        {question.question_type === 'MCQ' && (
          <McqInput
            options={Array.isArray(question.options) ? (question.options as ChoiceOption[]) : []}
            value={answers[question.id] as string[] | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}

        {question.question_type === 'TRUE_FALSE' && (
          <TrueFalseInput
            value={answers[question.id] as boolean | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}

        {question.question_type === 'FILL_IN' && (
          <FillInInput
            value={answers[question.id] as string | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}

        {question.question_type === 'DRAG_DROP' && (
          <DragDropInput
            options={
              typeof question.options === 'object' ? (question.options as DragDropOptions) : null
            }
            value={answers[question.id] as Record<string, string> | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}

        {question.question_type === 'MATCHING' && (
          <MatchingInput
            options={
              typeof question.options === 'object' ? (question.options as MatchingOptions) : null
            }
            value={answers[question.id] as Record<string, string> | undefined}
            onChange={(value) => onAnswer(question.id, value)}
          />
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button
          className="btn btn-secondary"
          disabled={currentIdx === 0}
          onClick={() => onNavigate(currentIdx - 1)}
        >
          {t('studentQuiz.prev')}
        </button>

        {currentIdx < questions.length - 1 ? (
          <button className="btn btn-primary" onClick={() => onNavigate(currentIdx + 1)}>
            {t('studentQuiz.next')}
          </button>
        ) : (
          <button
            className="btn btn-primary"
            onClick={() => void onSubmit()}
            disabled={submitting}
            style={{ background: 'var(--color-success)' }}
          >
            {submitting ? t('app.loading') : t('studentQuiz.submit')}
          </button>
        )}
      </div>
    </div>
  );
}

function McqInput({
  options,
  value,
  onChange,
}: {
  options: ChoiceOption[];
  value?: string[];
  onChange: (value: string[]) => void;
}) {
  const selected = value ?? [];

  function toggle(optionId: string) {
    onChange(
      selected.includes(optionId)
        ? selected.filter((item) => item !== optionId)
        : [...selected, optionId],
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {options.map((option) => (
        <label
          key={option.id}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 12px',
            borderRadius: 'var(--radius)',
            background: selected.includes(option.id)
              ? 'var(--color-surface-primary)'
              : 'var(--color-bg)',
            border: `1px solid ${selected.includes(option.id) ? 'var(--color-primary)' : 'var(--color-border)'}`,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          <input
            type="checkbox"
            checked={selected.includes(option.id)}
            onChange={() => toggle(option.id)}
            style={{ margin: 0 }}
          />
          <span style={{ fontSize: 14 }}>{option.text || option.id}</span>
        </label>
      ))}
    </div>
  );
}

function TrueFalseInput({
  value,
  onChange,
}: {
  value?: boolean;
  onChange: (value: boolean) => void;
}) {
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
          <input
            type="radio"
            checked={value === item}
            onChange={() => onChange(item)}
            style={{ display: 'none' }}
          />
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
  options: DragDropOptions | null;
  value?: Record<string, string>;
  onChange: (value: Record<string, string>) => void;
}) {
  const { t } = useTranslation();
  const items = options?.items || [];
  const zones = options?.zones || [];
  const current = value || {};

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
        {t('studentQuiz.dragDropHint')}
      </p>
      {items.map((item) => (
        <div
          key={item.id}
          style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}
        >
          <span style={{ fontSize: 13, fontWeight: 600, minWidth: 100 }}>
            {item.text || item.id}
          </span>
          <select
            className="filter-select"
            value={current[item.id] || ''}
            onChange={(event) => onChange({ ...current, [item.id]: event.target.value })}
            style={{ flex: 1 }}
          >
            <option value="">— {t('studentQuiz.selectZone')} —</option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.text || zone.id}
              </option>
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
  options: MatchingOptions | null;
  value?: Record<string, string>;
  onChange: (value: Record<string, string>) => void;
}) {
  const { t } = useTranslation();
  const left = options?.left || [];
  const right = options?.right || [];
  const current = value || {};

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
        {t('studentQuiz.matchHint')}
      </p>
      {left.map((item) => (
        <div
          key={item.id}
          style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}
        >
          <span style={{ fontSize: 13, fontWeight: 600, minWidth: 120 }}>
            {item.text || item.id}
          </span>
          <select
            className="filter-select"
            value={current[item.id] || ''}
            onChange={(event) => onChange({ ...current, [item.id]: event.target.value })}
            style={{ flex: 1 }}
          >
            <option value="">— {t('studentQuiz.selectMatch')} —</option>
            {right.map((option) => (
              <option key={option.id} value={option.id}>
                {option.text || option.id}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}
