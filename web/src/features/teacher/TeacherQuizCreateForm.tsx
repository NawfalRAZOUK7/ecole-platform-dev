import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { TeacherQuizQuestionEditor } from './TeacherQuizQuestionEditor';
import { QUIZ_QUESTION_TYPES, QUIZ_SUBJECTS, createDefaultQuestion, type TeacherQuizPayload } from './teacher-quiz.types';
import type { QuestionInput } from './teacher.service';

export interface TeacherQuizCreateFormProps {
  isSubmitting: boolean;
  onCancel: () => void;
  onCreate: (payload: TeacherQuizPayload) => Promise<void>;
}

export function TeacherQuizCreateForm({ isSubmitting, onCancel, onCreate }: TeacherQuizCreateFormProps) {
  const { t } = useTranslation();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState('');
  const [difficulty, setDifficulty] = useState('easy');
  const [timeLimit, setTimeLimit] = useState('');
  const [maxAttempts, setMaxAttempts] = useState('3');
  const [shuffle, setShuffle] = useState(false);
  const [questions, setQuestions] = useState<QuestionInput[]>([]);

  function addQuestion(type: string) {
    setQuestions((current) => [...current, createDefaultQuestion(type, current.length)]);
  }

  function updateQuestion(index: number, patch: Partial<QuestionInput>) {
    setQuestions((current) => current.map((question, questionIndex) => questionIndex === index ? { ...question, ...patch } : question));
  }

  function removeQuestion(index: number) {
    setQuestions((current) => current.filter((_, questionIndex) => questionIndex !== index));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || questions.length === 0) return;

    await onCreate({
      title: title.trim(),
      description: description.trim() || null,
      subject: subject || null,
      level_band: null,
      difficulty,
      time_limit_minutes: timeLimit ? parseInt(timeLimit, 10) : null,
      max_attempts: parseInt(maxAttempts, 10) || 3,
      shuffle_questions: shuffle,
      questions: questions.map((question, index) => ({ ...question, order: index })),
    });
  }

  return (
    <form className="card" style={{ padding: 20, maxWidth: 700 }} onSubmit={handleSubmit}>
      <h3 style={{ margin: '0 0 16px' }}>{t('teacherQuiz.createTitle')}</h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
        <div className="form-field">
          <label>{t('teacherQuiz.quizTitle')}</label>
          <input className="filter-input" value={title} onChange={(event) => setTitle(event.target.value)} required style={{ width: '100%' }} />
        </div>
        <div className="form-field">
          <label>{t('teacherQuiz.subject')}</label>
          <select className="filter-select" value={subject} onChange={(event) => setSubject(event.target.value)} style={{ width: '100%' }}>
            <option value="">-</option>
            {QUIZ_SUBJECTS.map((item) => <option key={item} value={item}>{t(`cms.subjects.${item}`, item)}</option>)}
          </select>
        </div>
        <div className="form-field">
          <label>{t('teacherQuiz.difficulty')}</label>
          <select className="filter-select" value={difficulty} onChange={(event) => setDifficulty(event.target.value)} style={{ width: '100%' }}>
            <option value="easy">{t('teacherQuiz.easy')}</option>
            <option value="medium">{t('teacherQuiz.medium')}</option>
            <option value="hard">{t('teacherQuiz.hard')}</option>
          </select>
        </div>
        <div className="form-field">
          <label>{t('teacherQuiz.timeLimit')}</label>
          <input type="number" className="filter-input" value={timeLimit} onChange={(event) => setTimeLimit(event.target.value)} placeholder="min" min="0" style={{ width: '100%' }} />
        </div>
        <div className="form-field">
          <label>{t('teacherQuiz.maxAttempts')}</label>
          <input type="number" className="filter-input" value={maxAttempts} onChange={(event) => setMaxAttempts(event.target.value)} min="1" style={{ width: '100%' }} />
        </div>
        <div className="form-field" style={{ display: 'flex', alignItems: 'center', gap: 8, paddingTop: 24 }}>
          <input type="checkbox" checked={shuffle} onChange={(event) => setShuffle(event.target.checked)} />
          <label style={{ margin: 0 }}>{t('teacherQuiz.shuffle')}</label>
        </div>
      </div>

      <div className="form-field" style={{ marginBottom: 16 }}>
        <label>{t('teacherQuiz.description')}</label>
        <input className="filter-input" value={description} onChange={(event) => setDescription(event.target.value)} style={{ width: '100%' }} />
      </div>

      <h4 style={{ margin: '0 0 8px' }}>{t('teacherQuiz.questions')} ({questions.length})</h4>

      {questions.map((question, index) => (
        <TeacherQuizQuestionEditor
          key={index}
          index={index}
          question={question}
          onRemove={() => removeQuestion(index)}
          onUpdateCorrectAnswer={(value) => updateQuestion(index, { correct_answer: value })}
          onUpdateExplanation={(value) => updateQuestion(index, { explanation: value })}
          onUpdateOptions={(choices) => updateQuestion(index, { options: { choices } })}
          onUpdatePoints={(value) => updateQuestion(index, { points: value })}
          onUpdateQuestionText={(value) => updateQuestion(index, { question_text: value })}
        />
      ))}

      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {QUIZ_QUESTION_TYPES.map((type) => <button key={type} type="button" className="btn btn-secondary" style={{ fontSize: 12 }} onClick={() => addQuestion(type)}>+ {t(`teacherQuiz.type_${type}`)}</button>)}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button type="submit" className="btn btn-primary" disabled={isSubmitting || !title.trim() || questions.length === 0}>
          {isSubmitting ? t('app.loading') : t('teacherQuiz.save')}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          {t('app.cancel')}
        </button>
      </div>
    </form>
  );
}
