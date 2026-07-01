import { QuestionEditor } from './QuestionEditor';
import type { Question } from '../model/quiz-builder.types';

interface QuestionListProps {
  questions: Question[];
  onChangeQuestion: (index: number, question: Question) => void;
  onMoveQuestion: (index: number, direction: -1 | 1) => void;
  onRemoveQuestion: (index: number) => void;
}

export function QuestionList({
  questions,
  onChangeQuestion,
  onMoveQuestion,
  onRemoveQuestion,
}: QuestionListProps) {
  return (
    <>
      {questions.map((question, index) => (
        <QuestionEditor
          key={question._key}
          index={index}
          question={question}
          total={questions.length}
          onChange={(updatedQuestion) => onChangeQuestion(index, updatedQuestion)}
          onMove={(direction) => onMoveQuestion(index, direction)}
          onRemove={() => onRemoveQuestion(index)}
        />
      ))}
    </>
  );
}
