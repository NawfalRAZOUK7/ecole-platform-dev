/**
 * Student Quiz Player — take quizzes with all 5 question types,
 * timer, navigation, results with explanations.
 *
 * Phase 10B — Student Quiz Player (Web)
 * API: GET /quizzes, GET /quizzes/{id}, POST /quizzes/{id}/start,
 *      POST /attempts/{id}/respond, POST /attempts/{id}/submit,
 *      GET /attempts/{id}/results
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { EmptyState } from '@/shared/ui/EmptyState';

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */
interface QuizListItem {
  id: string;
  title: string;
  description: string | null;
  subject: string | null;
  difficulty: string;
  time_limit_minutes: number | null;
  max_attempts: number;
  question_count: number;
  total_points: number;
  status: string;
}

interface Question {
  id: string;
  question_type: string;
  question_text: string;
  question_media_path: string | null;
  options: Record<string, unknown> | null;
  points: number;
  order: number;
}

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

interface Attempt {
  id: string;
  quiz_id: string;
  attempt_no: number;
  started_at: string | null;
  completed_at: string | null;
  score: number | null;
  max_score: number | null;
  status: string;
}

interface ResultResponse {
  question_id: string;
  question_type: string;
  question_text: string;
  student_answer: unknown;
  correct_answer: unknown;
  is_correct: boolean | null;
  points_earned: number | null;
  points: number;
  explanation: string | null;
}

interface AttemptResult {
  attempt: Attempt;
  responses: ResultResponse[];
}

type View = 'list' | 'playing' | 'results';

/* ------------------------------------------------------------------ */
/* Main                                                                */
/* ------------------------------------------------------------------ */
export function QuizPlayerPage() {
  const { t } = useTranslation();
  const [view, setView] = useState<View>('list');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // List
  const [quizzes, setQuizzes] = useState<QuizListItem[]>([]);

  // Playing
  const [currentQuiz, setCurrentQuiz] = useState<QuizListItem | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);

  // Results
  const [results, setResults] = useState<AttemptResult | null>(null);

  const fetchQuizzes = useCallback(async () => {
    try {
      const resp = await api.list<QuizListItem>('/quizzes', { status: 'published' });
      setQuizzes(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchQuizzes().finally(() => setLoading(false));
  }, [fetchQuizzes]);

  async function handleStartQuiz(quiz: QuizListItem) {
    setError(null);
    try {
      // Load quiz detail (questions)
      const detail = await api.get<{
        questions: Question[];
        [k: string]: unknown;
      }>(`/quizzes/${quiz.id}`);

      // Start attempt
      const attemptResp = await api.post<Attempt>(`/quizzes/${quiz.id}/start`);

      setCurrentQuiz(quiz);
      setQuestions(detail.data.questions);
      setAttempt(attemptResp.data);
      setCurrentIdx(0);
      setAnswers({});
      setView('playing');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  async function handleSubmitAnswer(questionId: string, answer: unknown) {
    if (!attempt) return;
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
    try {
      await api.post(`/attempts/${attempt.id}/respond`, {
        question_id: questionId,
        student_answer: answer,
      });
    } catch { /* save locally, will be sent on submit */ }
  }

  async function handleSubmitAttempt() {
    if (!attempt) return;
    setSubmitting(true);
    try {
      // Submit any remaining answers
      for (const q of questions) {
        if (answers[q.id] !== undefined) {
          try {
            await api.post(`/attempts/${attempt.id}/respond`, {
              question_id: q.id,
              student_answer: answers[q.id],
            });
          } catch { /* ignore duplicates */ }
        }
      }

      // Submit attempt for grading
      await api.post(`/attempts/${attempt.id}/submit`);

      // Fetch results
      const resultResp = await api.get<AttemptResult>(`/attempts/${attempt.id}/results`);
      setResults(resultResp.data);
      setView('results');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSubmitting(false);
    }
  }

  function handleBackToList() {
    setView('list');
    setCurrentQuiz(null);
    setQuestions([]);
    setAttempt(null);
    setResults(null);
    setAnswers({});
    fetchQuizzes();
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('studentQuiz.title')}</h1>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {view === 'list' && (
        <QuizList quizzes={quizzes} onStart={handleStartQuiz} />
      )}

      {view === 'playing' && attempt && currentQuiz && (
        <QuizPlay
          quiz={currentQuiz}
          questions={questions}
          attempt={attempt}
          currentIdx={currentIdx}
          answers={answers}
          submitting={submitting}
          onNavigate={setCurrentIdx}
          onAnswer={handleSubmitAnswer}
          onSubmit={handleSubmitAttempt}
        />
      )}

      {view === 'results' && results && (
        <QuizResults results={results} onBack={handleBackToList} />
      )}
    </div>
  );
}

/* ================================================================== */
/* Quiz List                                                           */
/* ================================================================== */
function QuizList({ quizzes, onStart }: { quizzes: QuizListItem[]; onStart: (q: QuizListItem) => void }) {
  const { t } = useTranslation();

  if (quizzes.length === 0) {
    return <EmptyState message={t('studentQuiz.empty')} />;
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
      {quizzes.map((q) => (
        <div key={q.id} className="card" style={{ padding: 16 }}>
          <h4 style={{ margin: '0 0 6px', fontSize: 15 }}>{q.title}</h4>
          {q.description && (
            <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0 0 8px' }}>
              {q.description.length > 100 ? q.description.slice(0, 100) + '...' : q.description}
            </p>
          )}
          <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
            {q.subject && <span style={{ marginRight: 8 }}>{t(`cms.subjects.${q.subject}`, q.subject)}</span>}
            <span style={{ marginRight: 8 }}>{q.difficulty}</span>
            <span>{q.question_count} {t('studentQuiz.questions')}</span>
            {q.time_limit_minutes && <span style={{ marginLeft: 8 }}>{q.time_limit_minutes} min</span>}
          </div>
          <button className="btn btn-primary" onClick={() => onStart(q)}>
            {t('studentQuiz.startQuiz')}
          </button>
        </div>
      ))}
    </div>
  );
}

/* ================================================================== */
/* Quiz Play                                                           */
/* ================================================================== */
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
  onAnswer: (qid: string, answer: unknown) => void;
  onSubmit: () => void;
}) {
  const { t } = useTranslation();
  const question = questions[currentIdx];
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  // Timer
  useEffect(() => {
    if (!quiz.time_limit_minutes || !attempt.started_at) return;
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
  }, [quiz.time_limit_minutes, attempt.started_at, onSubmit]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (!question) return null;

  return (
    <div>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <h3 style={{ margin: 0 }}>{quiz.title}</h3>
        {timeLeft !== null && (
          <span style={{
            fontSize: 16,
            fontWeight: 700,
            color: timeLeft < 60 ? 'var(--color-error)' : 'var(--color-text)',
            fontFamily: 'monospace',
          }}>
            {formatTime(timeLeft)}
          </span>
        )}
      </div>

      {/* Question navigation */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {questions.map((q, idx) => (
          <button
            key={q.id}
            className={`btn ${idx === currentIdx ? 'btn-primary' : answers[q.id] !== undefined ? 'btn-success' : 'btn-secondary'}`}
            style={{ width: 36, height: 36, padding: 0, fontSize: 13 }}
            onClick={() => onNavigate(idx)}
          >
            {idx + 1}
          </button>
        ))}
      </div>

      {/* Question card */}
      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
          {t('studentQuiz.question')} {currentIdx + 1}/{questions.length} — {question.points} {t('studentQuiz.pts')}
        </div>
        <h4 style={{ margin: '0 0 16px', fontSize: 16 }}>{question.question_text}</h4>

        {/* MCQ */}
        {question.question_type === 'mcq' && (
          <McqInput
            options={(question.options as McqOptions | null)?.choices || []}
            value={answers[question.id] as number | undefined}
            onChange={(v) => onAnswer(question.id, v)}
          />
        )}

        {/* True/False */}
        {question.question_type === 'true_false' && (
          <TrueFalseInput
            value={answers[question.id] as boolean | undefined}
            onChange={(v) => onAnswer(question.id, v)}
          />
        )}

        {/* Fill in blank */}
        {question.question_type === 'fill_in_blank' && (
          <FillInInput
            value={answers[question.id] as string | undefined}
            onChange={(v) => onAnswer(question.id, v)}
          />
        )}

        {/* Drag & Drop */}
        {question.question_type === 'drag_drop' && (
          <DragDropInput
            options={question.options}
            value={answers[question.id] as Record<string, string> | undefined}
            onChange={(v) => onAnswer(question.id, v)}
          />
        )}

        {/* Matching */}
        {question.question_type === 'matching' && (
          <MatchingInput
            options={question.options}
            value={answers[question.id] as Record<string, string> | undefined}
            onChange={(v) => onAnswer(question.id, v)}
          />
        )}
      </div>

      {/* Navigation buttons */}
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
            onClick={onSubmit}
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

/* ================================================================== */
/* Question Input Components                                           */
/* ================================================================== */

function McqInput({ options, value, onChange }: { options: string[]; value?: number; onChange: (v: number) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {options.map((opt, idx) => (
        <label
          key={idx}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 12px',
            borderRadius: 'var(--radius)',
            background: value === idx ? 'var(--color-primary-light, #e3f2fd)' : 'var(--color-bg)',
            border: `1px solid ${value === idx ? 'var(--color-primary)' : 'var(--color-border)'}`,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          <input type="radio" checked={value === idx} onChange={() => onChange(idx)} style={{ margin: 0 }} />
          <span style={{ fontSize: 14 }}>{opt}</span>
        </label>
      ))}
    </div>
  );
}

function TrueFalseInput({ value, onChange }: { value?: boolean; onChange: (v: boolean) => void }) {
  const { t } = useTranslation();
  return (
    <div style={{ display: 'flex', gap: 16 }}>
      {[true, false].map((v) => (
        <label
          key={String(v)}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            padding: '14px 16px',
            borderRadius: 'var(--radius)',
            background: value === v ? 'var(--color-primary-light, #e3f2fd)' : 'var(--color-bg)',
            border: `2px solid ${value === v ? 'var(--color-primary)' : 'var(--color-border)'}`,
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: 15,
            transition: 'all 0.2s',
          }}
        >
          <input type="radio" checked={value === v} onChange={() => onChange(v)} style={{ display: 'none' }} />
          {v ? t('studentQuiz.true') : t('studentQuiz.false')}
        </label>
      ))}
    </div>
  );
}

function FillInInput({ value, onChange }: { value?: string; onChange: (v: string) => void }) {
  const { t } = useTranslation();
  return (
    <input
      className="filter-input"
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
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
  onChange: (v: Record<string, string>) => void;
}) {
  const { t } = useTranslation();
  const items = (options as DragDropOptions | null)?.items || [];
  const zones = (options as DragDropOptions | null)?.zones || [];
  const current = value || {};

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8 }}>{t('studentQuiz.dragDropHint')}</p>
      {items.map((item: string, idx: number) => (
        <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 600, minWidth: 100 }}>{item}</span>
          <select
            className="filter-select"
            value={current[item] || ''}
            onChange={(e) => onChange({ ...current, [item]: e.target.value })}
            style={{ flex: 1 }}
          >
            <option value="">— {t('studentQuiz.selectZone')} —</option>
            {zones.map((z: string) => (
              <option key={z} value={z}>{z}</option>
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
  onChange: (v: Record<string, string>) => void;
}) {
  const { t } = useTranslation();
  const left = (options as MatchingOptions | null)?.left || [];
  const right = (options as MatchingOptions | null)?.right || [];
  const current = value || {};

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8 }}>{t('studentQuiz.matchHint')}</p>
      {left.map((l: string, idx: number) => (
        <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 600, minWidth: 120 }}>{l}</span>
          <select
            className="filter-select"
            value={current[l] || ''}
            onChange={(e) => onChange({ ...current, [l]: e.target.value })}
            style={{ flex: 1 }}
          >
            <option value="">— {t('studentQuiz.selectMatch')} —</option>
            {right.map((r: string) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}

/* ================================================================== */
/* Quiz Results                                                        */
/* ================================================================== */
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

      {/* Score summary */}
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

      {/* Question results */}
      {responses.map((r, idx) => (
        <div
          key={r.question_id}
          className="card"
          style={{
            padding: 16,
            marginBottom: 12,
            borderLeft: `4px solid ${r.is_correct ? 'var(--color-success)' : 'var(--color-error)'}`,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontWeight: 600, fontSize: 13 }}>Q{idx + 1} — {r.question_type}</span>
            <span style={{
              fontSize: 12,
              fontWeight: 600,
              color: r.is_correct ? 'var(--color-success)' : 'var(--color-error)',
            }}>
              {r.points_earned ?? 0}/{r.points} {t('studentQuiz.pts')}
            </span>
          </div>
          <p style={{ margin: '0 0 8px', fontSize: 14 }}>{r.question_text}</p>

          <div style={{ fontSize: 13, marginBottom: 4 }}>
            <strong>{t('studentQuiz.yourAnswer')}:</strong>{' '}
            <span style={{ color: r.is_correct ? 'var(--color-success)' : 'var(--color-error)' }}>
              {formatAnswer(r.student_answer)}
            </span>
          </div>
          {!r.is_correct && (
            <div style={{ fontSize: 13, marginBottom: 4 }}>
              <strong>{t('studentQuiz.correctAnswer')}:</strong>{' '}
              <span style={{ color: 'var(--color-success)' }}>{formatAnswer(r.correct_answer)}</span>
            </div>
          )}
          {r.explanation && (
            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 6, padding: 8, background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
              {r.explanation}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function formatAnswer(answer: unknown): string {
  if (answer === null || answer === undefined) return '—';
  if (typeof answer === 'boolean') return answer ? 'True' : 'False';
  if (typeof answer === 'object') return JSON.stringify(answer);
  return String(answer);
}
