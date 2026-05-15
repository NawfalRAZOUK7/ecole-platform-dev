import { useTranslation } from 'react-i18next';
import type { QuestionInput } from '@/features/lms/teacher/api/teacher.api';
import type { McqOptions } from '../model/teacher-quiz.types';

export interface TeacherQuizQuestionEditorProps {
  index: number;
  question: QuestionInput;
  onRemove: () => void;
  onUpdateCorrectAnswer: (value: unknown) => void;
  onUpdateExplanation: (value: string) => void;
  onUpdateOptions: (choices: string[]) => void;
  onUpdatePoints: (value: number) => void;
  onUpdateQuestionText: (value: string) => void;
}

export function TeacherQuizQuestionEditor({
  index,
  question,
  onRemove,
  onUpdateCorrectAnswer,
  onUpdateExplanation,
  onUpdateOptions,
  onUpdatePoints,
  onUpdateQuestionText,
}: TeacherQuizQuestionEditorProps) {
  const { t } = useTranslation();
  const choices = (question.options as McqOptions | null)?.choices || [];

  return (
    <div className="card" style={{ padding: 12, marginBottom: 12, background: 'var(--color-bg)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontWeight: 600, fontSize: 13 }}>
          Q{index + 1} - {t(`teacherQuiz.type_${question.question_type}`, question.question_type)}
        </span>
        <button
          type="button"
          className="btn btn-danger"
          style={{ fontSize: 11, padding: '2px 8px' }}
          onClick={onRemove}
        >
          {t('teacherQuiz.remove')}
        </button>
      </div>

      <div className="form-field" style={{ marginBottom: 8 }}>
        <input
          className="filter-input"
          placeholder={t('teacherQuiz.questionText')}
          value={question.question_text}
          onChange={(event) => onUpdateQuestionText(event.target.value)}
          required
          style={{ width: '100%' }}
        />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div className="form-field">
          <label style={{ fontSize: 11 }}>{t('teacherQuiz.points')}</label>
          <input
            type="number"
            className="filter-input"
            value={question.points}
            onChange={(event) => onUpdatePoints(parseInt(event.target.value, 10) || 1)}
            min="1"
            style={{ width: 60 }}
          />
        </div>
      </div>

      {question.question_type === 'mcq' ? (
        <div style={{ marginBottom: 8 }}>
          {choices.map((choice, choiceIndex) => (
            <div
              key={choiceIndex}
              style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}
            >
              <input
                type="radio"
                name={`q${index}_correct`}
                checked={question.correct_answer === choiceIndex}
                onChange={() => onUpdateCorrectAnswer(choiceIndex)}
              />
              <input
                className="filter-input"
                value={choice}
                onChange={(event) => {
                  const nextChoices = [...choices];
                  nextChoices[choiceIndex] = event.target.value;
                  onUpdateOptions(nextChoices);
                }}
                placeholder={`${t('teacherQuiz.option')} ${choiceIndex + 1}`}
                style={{ flex: 1 }}
              />
            </div>
          ))}
          <button
            type="button"
            className="btn btn-secondary"
            style={{ fontSize: 11, padding: '2px 8px', marginTop: 4 }}
            onClick={() => onUpdateOptions([...choices, ''])}
          >
            + {t('teacherQuiz.addOption')}
          </button>
        </div>
      ) : null}

      {question.question_type === 'true_false' ? (
        <div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
          <label>
            <input
              type="radio"
              checked={question.correct_answer === true}
              onChange={() => onUpdateCorrectAnswer(true)}
            />{' '}
            {t('teacherQuiz.true')}
          </label>
          <label>
            <input
              type="radio"
              checked={question.correct_answer === false}
              onChange={() => onUpdateCorrectAnswer(false)}
            />{' '}
            {t('teacherQuiz.false')}
          </label>
        </div>
      ) : null}

      {question.question_type === 'fill_in_blank' ? (
        <div className="form-field" style={{ marginBottom: 8 }}>
          <label style={{ fontSize: 11 }}>{t('teacherQuiz.correctAnswer')}</label>
          <input
            className="filter-input"
            value={typeof question.correct_answer === 'string' ? question.correct_answer : ''}
            onChange={(event) => onUpdateCorrectAnswer(event.target.value)}
            style={{ width: '100%' }}
          />
        </div>
      ) : null}

      <div className="form-field">
        <input
          className="filter-input"
          placeholder={t('teacherQuiz.explanation')}
          value={question.explanation}
          onChange={(event) => onUpdateExplanation(event.target.value)}
          style={{ width: '100%', fontSize: 12 }}
        />
      </div>
    </div>
  );
}
