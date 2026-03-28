/**
 * CMS Quiz Builder — create/edit quizzes with all 5 question types.
 *
 * Phase 10A — MCQ, True/False, Fill-in, Drag&Drop, Matching editors.
 * Question reorder, preview mode, quiz metadata form.
 */

import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import {
  useCmsQuiz,
  useCmsQuizzes,
  useCreateCmsQuiz,
  usePublishCmsQuiz,
  useUpdateCmsQuiz,
} from './useCms';

// --- Types ---

type QuestionType = 'MCQ' | 'TRUE_FALSE' | 'FILL_IN' | 'DRAG_DROP' | 'MATCHING';

interface McqOption {
  id: string;
  text: string;
}

interface DragDropItem {
  id: string;
  text: string;
}

interface MatchingPair {
  id: string;
  text: string;
}

interface Question {
  _key: string; // local client key for React
  question_type: QuestionType;
  question_text: string;
  options: unknown;
  correct_answer: unknown;
  points: number;
  order: number;
  explanation: string;
}

const QUESTION_TYPES: QuestionType[] = ['MCQ', 'TRUE_FALSE', 'FILL_IN', 'DRAG_DROP', 'MATCHING'];
const SUBJECTS = ['math', 'french', 'arabic', 'science', 'history', 'geography', 'english'];
const LEVELS = ['maternelle', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];

let keyCounter = 0;
function nextKey() { return `q_${++keyCounter}`; }

function defaultQuestion(type: QuestionType, order: number): Question {
  const base = { _key: nextKey(), question_type: type, question_text: '', points: 1, order, explanation: '' };
  switch (type) {
    case 'MCQ': return { ...base, options: [{ id: 'a', text: '' }, { id: 'b', text: '' }], correct_answer: [] };
    case 'TRUE_FALSE': return { ...base, options: null, correct_answer: true };
    case 'FILL_IN': return { ...base, options: null, correct_answer: [''] };
    case 'DRAG_DROP': return { ...base, options: { items: [{ id: 'i1', text: '' }], zones: [{ id: 'z1', text: '' }] }, correct_answer: {} };
    case 'MATCHING': return { ...base, options: { left: [{ id: 'l1', text: '' }], right: [{ id: 'r1', text: '' }] }, correct_answer: {} };
  }
}

// --- Quiz List (when no quizId) ---

function QuizListView({ onEdit, onCreate }: { onEdit: (id: string) => void; onCreate: () => void }) {
  const { t } = useTranslation();
  const quizzesQuery = useCmsQuizzes();
  const quizzes = quizzesQuery.data ?? [];

  if (quizzesQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 className="page-title">{t('cms.quiz.title')}</h1>
        <button className="btn btn-primary" onClick={onCreate}>{t('cms.quiz.create')}</button>
      </div>
      <ErrorBanner
        error={quizzesQuery.error instanceof Error ? quizzesQuery.error.message : null}
        onDismiss={() => {}}
        onRetry={() => void quizzesQuery.refetch()}
      />

      {quizzes.length === 0 ? (
        <p className="empty-state">{t('cms.quiz.empty')}</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {quizzes.map((q) => (
            <div key={q.id} className="card" style={{ padding: 16, cursor: 'pointer' }} onClick={() => onEdit(q.id)}>
              <h3 style={{ margin: '0 0 4px', fontSize: 15 }}>{q.title}</h3>
              {q.description && <p style={{ margin: '0 0 8px', fontSize: 13, color: 'var(--color-text-secondary)' }}>{q.description}</p>}
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', fontSize: 11 }}>
                <span className={`badge badge--${q.status}`}>{q.status}</span>
                {q.subject && <span className="badge">{q.subject}</span>}
                {q.level_band && <span className="badge">{q.level_band}</span>}
                {q.difficulty && <span className="badge">{q.difficulty}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// --- Question Editors ---

function McqEditor({ q, onChange }: { q: Question; onChange: (q: Question) => void }) {
  const { t } = useTranslation();
  const options = (q.options as McqOption[]) || [];
  const correct = (q.correct_answer as string[]) || [];

  function updateOption(index: number, text: string) {
    const newOpts = options.map((o, i) => (i === index ? { ...o, text } : o));
    onChange({ ...q, options: newOpts });
  }

  function addOption() {
    const id = String.fromCharCode(97 + options.length); // a, b, c, d...
    onChange({ ...q, options: [...options, { id, text: '' }] });
  }

  function removeOption(index: number) {
    const removed = options[index];
    const newOpts = options.filter((_, i) => i !== index);
    const newCorrect = correct.filter((c) => c !== removed.id);
    onChange({ ...q, options: newOpts, correct_answer: newCorrect });
  }

  function toggleCorrect(id: string) {
    const newCorrect = correct.includes(id) ? correct.filter((c) => c !== id) : [...correct, id];
    onChange({ ...q, correct_answer: newCorrect });
  }

  return (
    <div>
      {options.map((opt, i) => (
        <div key={opt.id} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={correct.includes(opt.id)}
              onChange={() => toggleCorrect(opt.id)}
            />
            {t('cms.quiz.correct')}
          </label>
          <input
            type="text"
            value={opt.text}
            onChange={(e) => updateOption(i, e.target.value)}
            placeholder={`${t('cms.quiz.option')} ${opt.id.toUpperCase()}`}
            style={{ flex: 1 }}
          />
          {options.length > 2 && (
            <button type="button" className="btn btn-sm btn-danger" onClick={() => removeOption(i)}>x</button>
          )}
        </div>
      ))}
      {options.length < 6 && (
        <button type="button" className="btn btn-sm" onClick={addOption}>+ {t('cms.quiz.addOption')}</button>
      )}
    </div>
  );
}

function TrueFalseEditor({ q, onChange }: { q: Question; onChange: (q: Question) => void }) {
  const { t } = useTranslation();
  const value = q.correct_answer as boolean;
  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <label style={{ cursor: 'pointer' }}>
        <input type="radio" checked={value === true} onChange={() => onChange({ ...q, correct_answer: true })} /> {t('cms.quiz.true')}
      </label>
      <label style={{ cursor: 'pointer' }}>
        <input type="radio" checked={value === false} onChange={() => onChange({ ...q, correct_answer: false })} /> {t('cms.quiz.false')}
      </label>
    </div>
  );
}

function FillInEditor({ q, onChange }: { q: Question; onChange: (q: Question) => void }) {
  const { t } = useTranslation();
  const answers = (q.correct_answer as string[]) || [''];

  function updateAnswer(index: number, text: string) {
    const newAnswers = answers.map((a, i) => (i === index ? text : a));
    onChange({ ...q, correct_answer: newAnswers });
  }

  function addAlternative() {
    onChange({ ...q, correct_answer: [...answers, ''] });
  }

  function removeAlternative(index: number) {
    onChange({ ...q, correct_answer: answers.filter((_, i) => i !== index) });
  }

  return (
    <div>
      {answers.map((ans, i) => (
        <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
          <input
            type="text"
            value={ans}
            onChange={(e) => updateAnswer(i, e.target.value)}
            placeholder={i === 0 ? t('cms.quiz.correctAnswer') : t('cms.quiz.alternative')}
            style={{ flex: 1 }}
          />
          {answers.length > 1 && (
            <button type="button" className="btn btn-sm btn-danger" onClick={() => removeAlternative(i)}>x</button>
          )}
        </div>
      ))}
      <button type="button" className="btn btn-sm" onClick={addAlternative}>+ {t('cms.quiz.addAlternative')}</button>
    </div>
  );
}

function DragDropEditor({ q, onChange }: { q: Question; onChange: (q: Question) => void }) {
  const { t } = useTranslation();
  const opts = q.options as { items: DragDropItem[]; zones: DragDropItem[] } || { items: [], zones: [] };
  const mapping = (q.correct_answer as Record<string, string>) || {};

  function addItem() {
    const id = `i${opts.items.length + 1}`;
    onChange({ ...q, options: { ...opts, items: [...opts.items, { id, text: '' }] } });
  }

  function addZone() {
    const id = `z${opts.zones.length + 1}`;
    onChange({ ...q, options: { ...opts, zones: [...opts.zones, { id, text: '' }] } });
  }

  function updateItem(index: number, text: string) {
    const newItems = opts.items.map((it, i) => (i === index ? { ...it, text } : it));
    onChange({ ...q, options: { ...opts, items: newItems } });
  }

  function updateZone(index: number, text: string) {
    const newZones = opts.zones.map((z, i) => (i === index ? { ...z, text } : z));
    onChange({ ...q, options: { ...opts, zones: newZones } });
  }

  function setMapping(itemId: string, zoneId: string) {
    onChange({ ...q, correct_answer: { ...mapping, [itemId]: zoneId } });
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <strong>{t('cms.quiz.items')}</strong>
          {opts.items.map((it, i) => (
            <div key={it.id} style={{ display: 'flex', gap: 4, marginTop: 4 }}>
              <input type="text" value={it.text} onChange={(e) => updateItem(i, e.target.value)} placeholder={it.id} style={{ flex: 1 }} />
              <select value={mapping[it.id] || ''} onChange={(e) => setMapping(it.id, e.target.value)}>
                <option value="">--</option>
                {opts.zones.map((z) => <option key={z.id} value={z.id}>{z.text || z.id}</option>)}
              </select>
            </div>
          ))}
          <button type="button" className="btn btn-sm" onClick={addItem} style={{ marginTop: 4 }}>+ {t('cms.quiz.addItem')}</button>
        </div>
        <div>
          <strong>{t('cms.quiz.zones')}</strong>
          {opts.zones.map((z, i) => (
            <div key={z.id} style={{ marginTop: 4 }}>
              <input type="text" value={z.text} onChange={(e) => updateZone(i, e.target.value)} placeholder={z.id} style={{ width: '100%' }} />
            </div>
          ))}
          <button type="button" className="btn btn-sm" onClick={addZone} style={{ marginTop: 4 }}>+ {t('cms.quiz.addZone')}</button>
        </div>
      </div>
    </div>
  );
}

function MatchingEditor({ q, onChange }: { q: Question; onChange: (q: Question) => void }) {
  const { t } = useTranslation();
  const opts = q.options as { left: MatchingPair[]; right: MatchingPair[] } || { left: [], right: [] };
  const mapping = (q.correct_answer as Record<string, string>) || {};

  function addLeft() {
    const id = `l${opts.left.length + 1}`;
    onChange({ ...q, options: { ...opts, left: [...opts.left, { id, text: '' }] } });
  }

  function addRight() {
    const id = `r${opts.right.length + 1}`;
    onChange({ ...q, options: { ...opts, right: [...opts.right, { id, text: '' }] } });
  }

  function updateLeft(index: number, text: string) {
    const newLeft = opts.left.map((p, i) => (i === index ? { ...p, text } : p));
    onChange({ ...q, options: { ...opts, left: newLeft } });
  }

  function updateRight(index: number, text: string) {
    const newRight = opts.right.map((p, i) => (i === index ? { ...p, text } : p));
    onChange({ ...q, options: { ...opts, right: newRight } });
  }

  function setMatch(leftId: string, rightId: string) {
    onChange({ ...q, correct_answer: { ...mapping, [leftId]: rightId } });
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <strong>{t('cms.quiz.leftColumn')}</strong>
          {opts.left.map((p, i) => (
            <div key={p.id} style={{ display: 'flex', gap: 4, marginTop: 4 }}>
              <input type="text" value={p.text} onChange={(e) => updateLeft(i, e.target.value)} placeholder={p.id} style={{ flex: 1 }} />
              <select value={mapping[p.id] || ''} onChange={(e) => setMatch(p.id, e.target.value)}>
                <option value="">--</option>
                {opts.right.map((r) => <option key={r.id} value={r.id}>{r.text || r.id}</option>)}
              </select>
            </div>
          ))}
          <button type="button" className="btn btn-sm" onClick={addLeft} style={{ marginTop: 4 }}>+ {t('cms.quiz.addPair')}</button>
        </div>
        <div>
          <strong>{t('cms.quiz.rightColumn')}</strong>
          {opts.right.map((p, i) => (
            <div key={p.id} style={{ marginTop: 4 }}>
              <input type="text" value={p.text} onChange={(e) => updateRight(i, e.target.value)} placeholder={p.id} style={{ width: '100%' }} />
            </div>
          ))}
          <button type="button" className="btn btn-sm" onClick={addRight} style={{ marginTop: 4 }}>+ {t('cms.quiz.addPair')}</button>
        </div>
      </div>
    </div>
  );
}

// --- Question Card ---

function QuestionCard({ q, index, total, onChange, onRemove, onMove }: {
  q: Question; index: number; total: number;
  onChange: (q: Question) => void; onRemove: () => void; onMove: (dir: -1 | 1) => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="card" style={{ padding: 16, marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <strong>Q{index + 1} — {t(`cms.quiz.types.${q.question_type}`, q.question_type)}</strong>
        <div style={{ display: 'flex', gap: 4 }}>
          {index > 0 && <button type="button" className="btn btn-sm" onClick={() => onMove(-1)}>&#x25B2;</button>}
          {index < total - 1 && <button type="button" className="btn btn-sm" onClick={() => onMove(1)}>&#x25BC;</button>}
          <button type="button" className="btn btn-sm btn-danger" onClick={onRemove}>x</button>
        </div>
      </div>

      <div className="form-field">
        <label>{t('cms.quiz.questionText')}</label>
        <textarea
          value={q.question_text}
          onChange={(e) => onChange({ ...q, question_text: e.target.value })}
          rows={2}
          placeholder={t('cms.quiz.questionTextPlaceholder')}
        />
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <div className="form-field" style={{ flex: 1 }}>
          <label>{t('cms.quiz.points')}</label>
          <input type="number" min={0} value={q.points} onChange={(e) => onChange({ ...q, points: Number(e.target.value) })} />
        </div>
        <div className="form-field" style={{ flex: 2 }}>
          <label>{t('cms.quiz.explanation')}</label>
          <input type="text" value={q.explanation} onChange={(e) => onChange({ ...q, explanation: e.target.value })} placeholder={t('cms.quiz.explanationPlaceholder')} />
        </div>
      </div>

      {/* Type-specific editor */}
      {q.question_type === 'MCQ' && <McqEditor q={q} onChange={onChange} />}
      {q.question_type === 'TRUE_FALSE' && <TrueFalseEditor q={q} onChange={onChange} />}
      {q.question_type === 'FILL_IN' && <FillInEditor q={q} onChange={onChange} />}
      {q.question_type === 'DRAG_DROP' && <DragDropEditor q={q} onChange={onChange} />}
      {q.question_type === 'MATCHING' && <MatchingEditor q={q} onChange={onChange} />}
    </div>
  );
}

// --- Preview Mode ---

function QuizPreview({ questions, onClose }: { questions: Question[]; onClose: () => void }) {
  const { t } = useTranslation();

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>{t('cms.quiz.preview')}</h2>
        <button className="btn" onClick={onClose}>{t('cms.quiz.exitPreview')}</button>
      </div>

      {questions.map((q, i) => (
        <div key={q._key} className="card" style={{ padding: 16, marginBottom: 12 }}>
          <p style={{ fontWeight: 600 }}>Q{i + 1}. {q.question_text} <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>({q.points} pts)</span></p>

          {q.question_type === 'MCQ' && (
            <div style={{ paddingInlineStart: 16 }}>
              {((q.options as McqOption[]) || []).map((opt) => (
                <div key={opt.id} style={{ padding: '4px 0' }}>
                  <label style={{ cursor: 'pointer' }}>
                    <input type="checkbox" disabled /> {opt.text || `(${opt.id})`}
                  </label>
                </div>
              ))}
            </div>
          )}

          {q.question_type === 'TRUE_FALSE' && (
            <div style={{ display: 'flex', gap: 16, paddingInlineStart: 16 }}>
              <label><input type="radio" disabled /> {t('cms.quiz.true')}</label>
              <label><input type="radio" disabled /> {t('cms.quiz.false')}</label>
            </div>
          )}

          {q.question_type === 'FILL_IN' && (
            <div style={{ paddingInlineStart: 16 }}>
              <input type="text" disabled placeholder={t('cms.quiz.fillInPlaceholder')} style={{ width: '100%', maxWidth: 300 }} />
            </div>
          )}

          {q.question_type === 'DRAG_DROP' && (
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', paddingInlineStart: 16 }}>
              [{t('cms.quiz.dragDropPreview')}]
            </p>
          )}

          {q.question_type === 'MATCHING' && (
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', paddingInlineStart: 16 }}>
              [{t('cms.quiz.matchingPreview')}]
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

// --- Main QuizBuilder ---

export function CmsQuizBuilderPage() {
  const { quizId } = useParams<{ quizId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const isEdit = !!quizId;
  const quizQuery = useCmsQuiz(quizId);
  const createQuizMutation = useCreateCmsQuiz();
  const updateQuizMutation = useUpdateCmsQuiz();
  const publishQuizMutation = usePublishCmsQuiz();

  // Quiz list vs builder
  const [showBuilder, setShowBuilder] = useState(isEdit);

  // Quiz metadata
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [quizSubject, setQuizSubject] = useState('');
  const [levelBand, setLevelBand] = useState('');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [timeLimit, setTimeLimit] = useState<number | ''>('');
  const [maxAttempts, setMaxAttempts] = useState(1);
  const [shuffle, setShuffle] = useState(false);

  // Questions
  const [questions, setQuestions] = useState<Question[]>([]);
  const [previewMode, setPreviewMode] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Load existing quiz
  useEffect(() => {
    if (!quizQuery.data) return;
    const q = quizQuery.data;
    setTitle(q.title);
    setDescription(q.description || '');
    setQuizSubject(q.subject || '');
    setLevelBand(q.level_band || '');
    setDifficulty(q.difficulty || 'MEDIUM');
    setTimeLimit(q.time_limit_minutes ?? '');
    setMaxAttempts(q.max_attempts);
    setShuffle(q.shuffle_questions);
    if (q.questions) {
      setQuestions(q.questions.map((qq, i) => ({
        _key: nextKey(),
        question_type: qq.question_type as QuestionType,
        question_text: qq.question_text,
        options: qq.options,
        correct_answer: qq.correct_answer,
        points: qq.points,
        order: i,
        explanation: qq.explanation || '',
      })));
    } else {
      setQuestions([]);
    }
    setShowBuilder(true);
  }, [quizQuery.data]);

  function addQuestion(type: QuestionType) {
    setQuestions((prev) => [...prev, defaultQuestion(type, prev.length)]);
  }

  function updateQuestion(index: number, updated: Question) {
    setQuestions((prev) => prev.map((q, i) => (i === index ? updated : q)));
  }

  function removeQuestion(index: number) {
    setQuestions((prev) => prev.filter((_, i) => i !== index).map((q, i) => ({ ...q, order: i })));
  }

  function moveQuestion(index: number, dir: -1 | 1) {
    setQuestions((prev) => {
      const arr = [...prev];
      const target = index + dir;
      if (target < 0 || target >= arr.length) return arr;
      [arr[index], arr[target]] = [arr[target], arr[index]];
      return arr.map((q, i) => ({ ...q, order: i }));
    });
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaved(false);

    const payload = {
      title,
      description: description || undefined,
      subject: quizSubject || undefined,
      level_band: levelBand || undefined,
      difficulty: difficulty || undefined,
      time_limit_minutes: timeLimit || undefined,
      max_attempts: maxAttempts,
      shuffle_questions: shuffle,
      questions: questions.map((q, i) => ({
        question_type: q.question_type,
        question_text: q.question_text,
        options: q.options,
        correct_answer: q.correct_answer,
        points: q.points,
        order: i,
        explanation: q.explanation || undefined,
      })),
    };

    try {
      if (isEdit) {
        await updateQuizMutation.mutateAsync({
          quizId: quizId!,
          payload,
        });
      } else {
        const createdQuiz = await createQuizMutation.mutateAsync(payload);
        navigate(`/cms/quizzes/${createdQuiz.id}/edit`, { replace: true });
      }
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  async function handlePublish() {
    if (!quizId) return;
    try {
      await publishQuizMutation.mutateAsync(quizId);
      navigate('/cms/quizzes');
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  const saving = createQuizMutation.isPending || updateQuizMutation.isPending;
  const loading = isEdit && quizQuery.isLoading;

  // Show quiz list if not in builder mode
  if (!showBuilder) {
    return (
      <QuizListView
        onEdit={(id) => navigate(`/cms/quizzes/${id}/edit`)}
        onCreate={() => { setShowBuilder(true); setTitle(''); setQuestions([]); }}
      />
    );
  }

  if (loading) return <LoadingState />;

  // Preview mode
  if (previewMode) {
    return <QuizPreview questions={questions} onClose={() => setPreviewMode(false)} />;
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 className="page-title">{isEdit ? t('cms.quiz.editTitle') : t('cms.quiz.createTitle')}</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          {questions.length > 0 && (
            <button className="btn" onClick={() => setPreviewMode(true)}>{t('cms.quiz.preview')}</button>
          )}
          <button className="btn" onClick={() => { setShowBuilder(false); navigate('/cms/quizzes'); }}>{t('app.back')}</button>
        </div>
      </div>

      <ErrorBanner
        error={error || (quizQuery.error instanceof Error ? quizQuery.error.message : null)}
        onDismiss={() => setError(null)}
      />
      {saved && <div className="alert alert-success" style={{ marginBottom: 16, padding: 12, borderRadius: 8 }}>{t('cms.quiz.saved')}</div>}

      <form onSubmit={handleSave}>
        {/* Quiz metadata */}
        <div className="card" style={{ padding: 16, marginBottom: 16 }}>
          <h2 style={{ marginTop: 0, fontSize: 16 }}>{t('cms.quiz.metadata')}</h2>
          <div className="form-field">
            <label>{t('cms.quiz.quizTitle')}</label>
            <input type="text" required maxLength={300} value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="form-field">
            <label>{t('cms.upload.description')}</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
            <div className="form-field">
              <label>{t('cms.upload.subject')}</label>
              <select value={quizSubject} onChange={(e) => setQuizSubject(e.target.value)}>
                <option value="">--</option>
                {SUBJECTS.map((s) => <option key={s} value={s}>{t(`cms.subjects.${s}`, s)}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label>{t('cms.upload.level')}</label>
              <select value={levelBand} onChange={(e) => setLevelBand(e.target.value)}>
                <option value="">--</option>
                {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label>{t('cms.quiz.difficulty')}</label>
              <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                <option value="EASY">{t('cms.quiz.easy')}</option>
                <option value="MEDIUM">{t('cms.quiz.medium')}</option>
                <option value="HARD">{t('cms.quiz.hard')}</option>
              </select>
            </div>
            <div className="form-field">
              <label>{t('cms.quiz.timeLimit')}</label>
              <input type="number" min={0} value={timeLimit} onChange={(e) => setTimeLimit(e.target.value ? Number(e.target.value) : '')} placeholder="min" />
            </div>
            <div className="form-field">
              <label>{t('cms.quiz.maxAttempts')}</label>
              <input type="number" min={1} value={maxAttempts} onChange={(e) => setMaxAttempts(Number(e.target.value))} />
            </div>
            <div className="form-field" style={{ display: 'flex', alignItems: 'center', gap: 8, paddingTop: 20 }}>
              <input type="checkbox" checked={shuffle} onChange={(e) => setShuffle(e.target.checked)} />
              <label>{t('cms.quiz.shuffle')}</label>
            </div>
          </div>
        </div>

        {/* Questions */}
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>{t('cms.quiz.questions')} ({questions.length})</h2>

        {questions.map((q, i) => (
          <QuestionCard
            key={q._key}
            q={q}
            index={i}
            total={questions.length}
            onChange={(updated) => updateQuestion(i, updated)}
            onRemove={() => removeQuestion(i)}
            onMove={(dir) => moveQuestion(i, dir)}
          />
        ))}

        {/* Add question buttons */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
          {QUESTION_TYPES.map((qt) => (
            <button key={qt} type="button" className="btn btn-sm" onClick={() => addQuestion(qt)}>
              + {t(`cms.quiz.types.${qt}`, qt)}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit" className="btn btn-primary" disabled={saving || !title}>
            {saving ? t('app.loading') : t('app.save')}
          </button>
          {isEdit && (
            <button type="button" className="btn btn-primary" onClick={handlePublish}>
              {t('cms.quiz.publish')}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
