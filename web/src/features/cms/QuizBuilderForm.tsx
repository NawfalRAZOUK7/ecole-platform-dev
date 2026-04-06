import { useTranslation } from 'react-i18next';
import { LEVELS, QUESTION_TYPES, SUBJECTS, type QuestionType } from './quiz-builder.types';

interface QuizBuilderFormProps {
  description: string;
  difficulty: string;
  isEdit: boolean;
  levelBand: string;
  maxAttempts: number;
  previewEnabled: boolean;
  questionCount: number;
  quizSubject: string;
  saving: boolean;
  shuffle: boolean;
  timeLimit: number | '';
  title: string;
  onAddQuestion: (type: QuestionType) => void;
  onBack: () => void;
  onChangeDescription: (value: string) => void;
  onChangeDifficulty: (value: string) => void;
  onChangeLevelBand: (value: string) => void;
  onChangeMaxAttempts: (value: number) => void;
  onChangeQuizSubject: (value: string) => void;
  onChangeShuffle: (value: boolean) => void;
  onChangeTimeLimit: (value: number | '') => void;
  onChangeTitle: (value: string) => void;
  onPreview: () => void;
}

export function QuizBuilderForm({
  description,
  difficulty,
  isEdit,
  levelBand,
  maxAttempts,
  previewEnabled,
  questionCount,
  quizSubject,
  saving,
  shuffle,
  timeLimit,
  title,
  onAddQuestion,
  onBack,
  onChangeDescription,
  onChangeDifficulty,
  onChangeLevelBand,
  onChangeMaxAttempts,
  onChangeQuizSubject,
  onChangeShuffle,
  onChangeTimeLimit,
  onChangeTitle,
  onPreview,
}: QuizBuilderFormProps) {
  const { t } = useTranslation();

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 className="page-title">{isEdit ? t('cms.quiz.editTitle') : t('cms.quiz.createTitle')}</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          {previewEnabled && <button className="btn" onClick={onPreview}>{t('cms.quiz.preview')}</button>}
          <button className="btn" onClick={onBack}>{t('app.back')}</button>
        </div>
      </div>

      <div className="card" style={{ padding: 16, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0, fontSize: 16 }}>{t('cms.quiz.metadata')}</h2>
        <label className="form-field"><span>{t('cms.quiz.quizTitle')}</span><input type="text" required maxLength={300} value={title} onChange={(event) => onChangeTitle(event.target.value)} /></label>
        <label className="form-field"><span>{t('cms.upload.description')}</span><textarea value={description} onChange={(event) => onChangeDescription(event.target.value)} rows={2} /></label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
          <label className="form-field"><span>{t('cms.upload.subject')}</span><select value={quizSubject} onChange={(event) => onChangeQuizSubject(event.target.value)}><option value="">--</option>{SUBJECTS.map((subject) => <option key={subject} value={subject}>{t(`cms.subjects.${subject}`, subject)}</option>)}</select></label>
          <label className="form-field"><span>{t('cms.upload.level')}</span><select value={levelBand} onChange={(event) => onChangeLevelBand(event.target.value)}><option value="">--</option>{LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}</select></label>
          <label className="form-field"><span>{t('cms.quiz.difficulty')}</span><select value={difficulty} onChange={(event) => onChangeDifficulty(event.target.value)}><option value="EASY">{t('cms.quiz.easy')}</option><option value="MEDIUM">{t('cms.quiz.medium')}</option><option value="HARD">{t('cms.quiz.hard')}</option></select></label>
          <label className="form-field"><span>{t('cms.quiz.timeLimit')}</span><input type="number" min={0} value={timeLimit} onChange={(event) => onChangeTimeLimit(event.target.value ? Number(event.target.value) : '')} placeholder="min" /></label>
          <label className="form-field"><span>{t('cms.quiz.maxAttempts')}</span><input type="number" min={1} value={maxAttempts} onChange={(event) => onChangeMaxAttempts(Number(event.target.value))} /></label>
          <label className="form-field" style={{ display: 'flex', alignItems: 'center', gap: 8, paddingTop: 20 }}><input type="checkbox" checked={shuffle} onChange={(event) => onChangeShuffle(event.target.checked)} /><span>{t('cms.quiz.shuffle')}</span></label>
        </div>
      </div>

      <h2 style={{ fontSize: 16, marginBottom: 12 }}>{t('cms.quiz.questions')} ({questionCount})</h2>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        {QUESTION_TYPES.map((type) => <button key={type} type="button" className="btn btn-sm" onClick={() => onAddQuestion(type)}>+ {t(`cms.quiz.types.${type}`, type)}</button>)}
      </div>

      {saving && <div style={{ marginBottom: 12, fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('app.loading')}</div>}
    </>
  );
}
