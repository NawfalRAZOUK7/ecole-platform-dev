import { useTranslation } from 'react-i18next';
import type { McqOption, Question } from '../model/quiz-builder.types';

interface QuizPreviewProps {
  onClose: () => void;
  questions: Question[];
}

export function QuizPreview({ onClose, questions }: QuizPreviewProps) {
  const { t } = useTranslation();

  return (
    <div className="page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <h2>{t('cms.quiz.preview')}</h2>
        <button className="btn" onClick={onClose}>
          {t('cms.quiz.exitPreview')}
        </button>
      </div>

      {questions.map((question, index) => (
        <div key={question._key} className="card" style={{ padding: 16, marginBottom: 12 }}>
          <p style={{ fontWeight: 600 }}>
            Q{index + 1}. {question.question_text}{' '}
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              ({question.points} pts)
            </span>
          </p>
          {question.question_type === 'MCQ' && (
            <div style={{ paddingInlineStart: 16 }}>
              {((question.options as McqOption[]) || []).map((option) => (
                <div key={option.id} style={{ padding: '4px 0' }}>
                  <label style={{ cursor: 'pointer' }}>
                    <input type="checkbox" disabled /> {option.text || `(${option.id})`}
                  </label>
                </div>
              ))}
            </div>
          )}
          {question.question_type === 'TRUE_FALSE' && (
            <div style={{ display: 'flex', gap: 16, paddingInlineStart: 16 }}>
              <label>
                <input type="radio" disabled /> {t('cms.quiz.true')}
              </label>
              <label>
                <input type="radio" disabled /> {t('cms.quiz.false')}
              </label>
            </div>
          )}
          {question.question_type === 'FILL_IN' && (
            <div style={{ paddingInlineStart: 16 }}>
              <input
                type="text"
                disabled
                placeholder={t('cms.quiz.fillInPlaceholder')}
                style={{ width: '100%', maxWidth: 300 }}
              />
            </div>
          )}
          {question.question_type === 'DRAG_DROP' && (
            <p
              style={{ fontSize: 13, color: 'var(--color-text-secondary)', paddingInlineStart: 16 }}
            >
              [{t('cms.quiz.dragDropPreview')}]
            </p>
          )}
          {question.question_type === 'MATCHING' && (
            <p
              style={{ fontSize: 13, color: 'var(--color-text-secondary)', paddingInlineStart: 16 }}
            >
              [{t('cms.quiz.matchingPreview')}]
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
