import { useTranslation } from 'react-i18next';
import { QuestionMappingEditor } from './QuestionMappingEditor';
import { QuestionOptionEditor } from './QuestionOptionEditor';
import type { Question } from '../model/quiz-builder.types';

interface QuestionEditorProps {
  index: number;
  question: Question;
  total: number;
  onChange: (question: Question) => void;
  onMove: (direction: -1 | 1) => void;
  onRemove: () => void;
}

export function QuestionEditor({
  index,
  question,
  total,
  onChange,
  onMove,
  onRemove,
}: QuestionEditorProps) {
  const { t } = useTranslation();

  return (
    <div className="card" style={{ padding: 16, marginBottom: 12 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8,
        }}
      >
        <strong>
          Q{index + 1} — {t(`cms.quiz.types.${question.question_type}`, question.question_type)}
        </strong>
        <div style={{ display: 'flex', gap: 4 }}>
          {index > 0 && (
            <button type="button" className="btn btn-sm" onClick={() => onMove(-1)}>
              &#x25B2;
            </button>
          )}
          {index < total - 1 && (
            <button type="button" className="btn btn-sm" onClick={() => onMove(1)}>
              &#x25BC;
            </button>
          )}
          <button type="button" className="btn btn-sm btn-danger" onClick={onRemove}>
            x
          </button>
        </div>
      </div>

      <label className="form-field">
        <span>{t('cms.quiz.questionText')}</span>
        <textarea
          value={question.question_text}
          onChange={(event) => onChange({ ...question, question_text: event.target.value })}
          rows={2}
          placeholder={t('cms.quiz.questionTextPlaceholder')}
        />
      </label>

      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <label className="form-field" style={{ flex: 1 }}>
          <span>{t('cms.quiz.points')}</span>
          <input
            type="number"
            min={0}
            value={question.points}
            onChange={(event) => onChange({ ...question, points: Number(event.target.value) })}
          />
        </label>
        <label className="form-field" style={{ flex: 2 }}>
          <span>{t('cms.quiz.explanation')}</span>
          <input
            type="text"
            value={question.explanation}
            onChange={(event) => onChange({ ...question, explanation: event.target.value })}
            placeholder={t('cms.quiz.explanationPlaceholder')}
          />
        </label>
      </div>

      {['MCQ', 'TRUE_FALSE', 'FILL_IN'].includes(question.question_type) ? (
        <QuestionOptionEditor question={question} onChange={onChange} />
      ) : (
        <QuestionMappingEditor question={question} onChange={onChange} />
      )}
    </div>
  );
}
