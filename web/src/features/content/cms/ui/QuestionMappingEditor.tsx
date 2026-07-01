import { useTranslation } from 'react-i18next';
import type { DragDropItem, MatchingPair, Question } from '../model/quiz-builder.types';

interface QuestionMappingEditorProps {
  question: Question;
  onChange: (question: Question) => void;
}

export function QuestionMappingEditor({ question, onChange }: QuestionMappingEditorProps) {
  if (question.question_type === 'DRAG_DROP') {
    return <DragDropEditor question={question} onChange={onChange} />;
  }
  return <MatchingEditor question={question} onChange={onChange} />;
}

function DragDropEditor({ question, onChange }: QuestionMappingEditorProps) {
  const { t } = useTranslation();
  const options = (question.options as { items: DragDropItem[]; zones: DragDropItem[] }) || {
    items: [],
    zones: [],
  };
  const mapping = (question.correct_answer as Record<string, string>) || {};

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
      <div>
        <strong>{t('cms.quiz.items')}</strong>
        {options.items.map((item, index) => (
          <div key={item.id} style={{ display: 'flex', gap: 4, marginTop: 4 }}>
            <input
              type="text"
              value={item.text}
              onChange={(event) =>
                onChange({
                  ...question,
                  options: {
                    ...options,
                    items: options.items.map((current, itemIndex) =>
                      itemIndex === index ? { ...current, text: event.target.value } : current,
                    ),
                  },
                })
              }
              placeholder={item.id}
              style={{ flex: 1 }}
            />
            <select
              value={mapping[item.id] || ''}
              onChange={(event) =>
                onChange({
                  ...question,
                  correct_answer: { ...mapping, [item.id]: event.target.value },
                })
              }
            >
              <option value="">--</option>
              {options.zones.map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {zone.text || zone.id}
                </option>
              ))}
            </select>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-sm"
          onClick={() =>
            onChange({
              ...question,
              options: {
                ...options,
                items: [...options.items, { id: `i${options.items.length + 1}`, text: '' }],
              },
            })
          }
          style={{ marginTop: 4 }}
        >
          + {t('cms.quiz.addItem')}
        </button>
      </div>
      <div>
        <strong>{t('cms.quiz.zones')}</strong>
        {options.zones.map((zone, index) => (
          <div key={zone.id} style={{ marginTop: 4 }}>
            <input
              type="text"
              value={zone.text}
              onChange={(event) =>
                onChange({
                  ...question,
                  options: {
                    ...options,
                    zones: options.zones.map((current, zoneIndex) =>
                      zoneIndex === index ? { ...current, text: event.target.value } : current,
                    ),
                  },
                })
              }
              placeholder={zone.id}
              style={{ width: '100%' }}
            />
          </div>
        ))}
        <button
          type="button"
          className="btn btn-sm"
          onClick={() =>
            onChange({
              ...question,
              options: {
                ...options,
                zones: [...options.zones, { id: `z${options.zones.length + 1}`, text: '' }],
              },
            })
          }
          style={{ marginTop: 4 }}
        >
          + {t('cms.quiz.addZone')}
        </button>
      </div>
    </div>
  );
}

function MatchingEditor({ question, onChange }: QuestionMappingEditorProps) {
  const { t } = useTranslation();
  const options = (question.options as { left: MatchingPair[]; right: MatchingPair[] }) || {
    left: [],
    right: [],
  };
  const mapping = (question.correct_answer as Record<string, string>) || {};

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
      <div>
        <strong>{t('cms.quiz.leftColumn')}</strong>
        {options.left.map((item, index) => (
          <div key={item.id} style={{ display: 'flex', gap: 4, marginTop: 4 }}>
            <input
              type="text"
              value={item.text}
              onChange={(event) =>
                onChange({
                  ...question,
                  options: {
                    ...options,
                    left: options.left.map((current, itemIndex) =>
                      itemIndex === index ? { ...current, text: event.target.value } : current,
                    ),
                  },
                })
              }
              placeholder={item.id}
              style={{ flex: 1 }}
            />
            <select
              value={mapping[item.id] || ''}
              onChange={(event) =>
                onChange({
                  ...question,
                  correct_answer: { ...mapping, [item.id]: event.target.value },
                })
              }
            >
              <option value="">--</option>
              {options.right.map((pair) => (
                <option key={pair.id} value={pair.id}>
                  {pair.text || pair.id}
                </option>
              ))}
            </select>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-sm"
          onClick={() =>
            onChange({
              ...question,
              options: {
                ...options,
                left: [...options.left, { id: `l${options.left.length + 1}`, text: '' }],
              },
            })
          }
          style={{ marginTop: 4 }}
        >
          + {t('cms.quiz.addPair')}
        </button>
      </div>
      <div>
        <strong>{t('cms.quiz.rightColumn')}</strong>
        {options.right.map((item, index) => (
          <div key={item.id} style={{ marginTop: 4 }}>
            <input
              type="text"
              value={item.text}
              onChange={(event) =>
                onChange({
                  ...question,
                  options: {
                    ...options,
                    right: options.right.map((current, itemIndex) =>
                      itemIndex === index ? { ...current, text: event.target.value } : current,
                    ),
                  },
                })
              }
              placeholder={item.id}
              style={{ width: '100%' }}
            />
          </div>
        ))}
        <button
          type="button"
          className="btn btn-sm"
          onClick={() =>
            onChange({
              ...question,
              options: {
                ...options,
                right: [...options.right, { id: `r${options.right.length + 1}`, text: '' }],
              },
            })
          }
          style={{ marginTop: 4 }}
        >
          + {t('cms.quiz.addPair')}
        </button>
      </div>
    </div>
  );
}
