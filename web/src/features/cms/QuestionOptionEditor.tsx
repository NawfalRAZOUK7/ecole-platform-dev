import { useTranslation } from 'react-i18next';
import type { McqOption, Question } from './quiz-builder.types';

interface QuestionOptionEditorProps {
  question: Question;
  onChange: (question: Question) => void;
}

export function QuestionOptionEditor({ question, onChange }: QuestionOptionEditorProps) {
  if (question.question_type === 'MCQ') {
    return <McqEditor question={question} onChange={onChange} />;
  }
  if (question.question_type === 'TRUE_FALSE') {
    return <TrueFalseEditor question={question} onChange={onChange} />;
  }
  return <FillInEditor question={question} onChange={onChange} />;
}

function McqEditor({ question, onChange }: QuestionOptionEditorProps) {
  const { t } = useTranslation();
  const options = (question.options as McqOption[]) || [];
  const correct = (question.correct_answer as string[]) || [];

  function updateOption(index: number, text: string) {
    onChange({ ...question, options: options.map((option, optionIndex) => (optionIndex === index ? { ...option, text } : option)) });
  }

  function removeOption(index: number) {
    const removed = options[index];
    const nextOptions = options.filter((_, optionIndex) => optionIndex !== index);
    onChange({ ...question, options: nextOptions, correct_answer: correct.filter((item) => item !== removed.id) });
  }

  return (
    <div>
      {options.map((option, index) => (
        <div key={option.id} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
            <input type="checkbox" checked={correct.includes(option.id)} onChange={() => onChange({ ...question, correct_answer: correct.includes(option.id) ? correct.filter((item) => item !== option.id) : [...correct, option.id] })} />
            {t('cms.quiz.correct')}
          </label>
          <input type="text" value={option.text} onChange={(event) => updateOption(index, event.target.value)} placeholder={`${t('cms.quiz.option')} ${option.id.toUpperCase()}`} style={{ flex: 1 }} />
          {options.length > 2 && <button type="button" className="btn btn-sm btn-danger" onClick={() => removeOption(index)}>x</button>}
        </div>
      ))}
      {options.length < 6 && (
        <button type="button" className="btn btn-sm" onClick={() => onChange({ ...question, options: [...options, { id: String.fromCharCode(97 + options.length), text: '' }] })}>
          + {t('cms.quiz.addOption')}
        </button>
      )}
    </div>
  );
}

function TrueFalseEditor({ question, onChange }: QuestionOptionEditorProps) {
  const { t } = useTranslation();
  const value = question.correct_answer as boolean;

  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <label style={{ cursor: 'pointer' }}><input type="radio" checked={value === true} onChange={() => onChange({ ...question, correct_answer: true })} /> {t('cms.quiz.true')}</label>
      <label style={{ cursor: 'pointer' }}><input type="radio" checked={value === false} onChange={() => onChange({ ...question, correct_answer: false })} /> {t('cms.quiz.false')}</label>
    </div>
  );
}

function FillInEditor({ question, onChange }: QuestionOptionEditorProps) {
  const { t } = useTranslation();
  const answers = (question.correct_answer as string[]) || [''];

  return (
    <div>
      {answers.map((answer, index) => (
        <div key={index} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
          <input type="text" value={answer} onChange={(event) => onChange({ ...question, correct_answer: answers.map((item, answerIndex) => (answerIndex === index ? event.target.value : item)) })} placeholder={index === 0 ? t('cms.quiz.correctAnswer') : t('cms.quiz.alternative')} style={{ flex: 1 }} />
          {answers.length > 1 && <button type="button" className="btn btn-sm btn-danger" onClick={() => onChange({ ...question, correct_answer: answers.filter((_, answerIndex) => answerIndex !== index) })}>x</button>}
        </div>
      ))}
      <button type="button" className="btn btn-sm" onClick={() => onChange({ ...question, correct_answer: [...answers, ''] })}>+ {t('cms.quiz.addAlternative')}</button>
    </div>
  );
}
