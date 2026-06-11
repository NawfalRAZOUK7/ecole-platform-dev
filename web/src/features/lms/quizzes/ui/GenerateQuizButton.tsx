/**
 * GenerateQuizButton — teacher-triggered quiz generation from a content item
 * (Feature B). Opens a dialog where the teacher chooses question types, count,
 * and sources (deterministic templates and/or AI), then creates a DRAFT quiz
 * to review and publish. Localized via i18n (fr/en/ar).
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  quizzesService,
  type GenerateFromContentResult,
  type QuizQuestionType,
  type QuizQuestionSource,
} from '@/features/lms/quizzes/api/quizzes.api';

const TYPE_KEYS: { value: QuizQuestionType; key: string; fallback: string }[] = [
  { value: 'MCQ', key: 'generateQuiz.typeMcq', fallback: 'QCM' },
  { value: 'TRUE_FALSE', key: 'generateQuiz.typeTrueFalse', fallback: 'Vrai / Faux' },
  { value: 'FILL_IN', key: 'generateQuiz.typeFillIn', fallback: 'Texte à trous' },
  { value: 'MATCHING', key: 'generateQuiz.typeMatching', fallback: 'Association (IA)' },
];

const SOURCE_KEYS: {
  value: QuizQuestionSource;
  key: string;
  fallback: string;
  hintKey: string;
  hintFallback: string;
}[] = [
  {
    value: 'template',
    key: 'generateQuiz.sourceTemplate',
    fallback: 'Modèles',
    hintKey: 'generateQuiz.sourceTemplateHint',
    hintFallback: 'déterministe, gratuit',
  },
  {
    value: 'ai',
    key: 'generateQuiz.sourceAi',
    fallback: 'IA',
    hintKey: 'generateQuiz.sourceAiHint',
    hintFallback: 'via le fournisseur configuré',
  },
];

interface Props {
  contentId: string;
  contentTitle?: string;
}

export function GenerateQuizButton({ contentId, contentTitle }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" className="btn btn-secondary" onClick={() => setOpen(true)}>
        🧩 {t('generateQuiz.button', 'Générer un quiz')}
      </button>
      {open && (
        <GenerateQuizDialog
          contentId={contentId}
          contentTitle={contentTitle}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

function GenerateQuizDialog({ contentId, contentTitle, onClose }: Props & { onClose: () => void }) {
  const { t } = useTranslation();
  const [types, setTypes] = useState<QuizQuestionType[]>(['MCQ', 'TRUE_FALSE', 'FILL_IN']);
  const [count, setCount] = useState(5);
  const [sources, setSources] = useState<QuizQuestionSource[]>(['template']);

  const mutation = useMutation<GenerateFromContentResult, Error>({
    mutationFn: async () =>
      (
        await quizzesService.generateFromContent(contentId, {
          question_types: types,
          count,
          sources,
        })
      ).data,
  });

  function toggleType(value: QuizQuestionType) {
    setTypes((prev) => (prev.includes(value) ? prev.filter((x) => x !== value) : [...prev, value]));
  }
  function toggleSource(value: QuizQuestionSource) {
    setSources((prev) =>
      prev.includes(value) ? prev.filter((x) => x !== value) : [...prev, value],
    );
  }

  const result = mutation.data;
  const canSubmit = types.length > 0 && sources.length > 0 && !mutation.isPending;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: 16,
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{ maxWidth: 520, width: '100%', maxHeight: '90vh', overflow: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ marginTop: 0, marginBottom: 4, fontSize: 18 }}>
          {t('generateQuiz.title', 'Générer un quiz')}
        </h3>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
          {t('generateQuiz.subtitle', 'Depuis : {{title}}. Un brouillon sera créé, à revoir avant publication.', {
            title: contentTitle ?? t('generateQuiz.thisContent', 'ce contenu'),
          })}
        </p>

        {!result && (
          <>
            <fieldset style={{ border: 'none', padding: 0, marginBottom: 16 }}>
              <legend style={{ fontWeight: 600, marginBottom: 8 }}>
                {t('generateQuiz.types', 'Types de questions')}
              </legend>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {TYPE_KEYS.map((opt) => (
                  <label key={opt.value} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 14 }}>
                    <input type="checkbox" checked={types.includes(opt.value)} onChange={() => toggleType(opt.value)} />
                    {t(opt.key, opt.fallback)}
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="form-field" style={{ marginBottom: 16 }}>
              <label>
                {t('generateQuiz.count', 'Nombre de questions')} : {count}
              </label>
              <input
                type="range"
                min={1}
                max={20}
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <fieldset style={{ border: 'none', padding: 0, marginBottom: 20 }}>
              <legend style={{ fontWeight: 600, marginBottom: 8 }}>
                {t('generateQuiz.sources', 'Sources')}
              </legend>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                {SOURCE_KEYS.map((opt) => (
                  <label key={opt.value} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 14 }}>
                    <input
                      type="checkbox"
                      checked={sources.includes(opt.value)}
                      onChange={() => toggleSource(opt.value)}
                    />
                    {t(opt.key, opt.fallback)}{' '}
                    <span style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>
                      ({t(opt.hintKey, opt.hintFallback)})
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>

            {mutation.isError && (
              <p style={{ color: 'var(--color-danger)', fontSize: 13, marginBottom: 12 }}>
                {mutation.error.message || t('generateQuiz.error', 'La génération a échoué.')}
              </p>
            )}

            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                {t('app.cancel', 'Annuler')}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                disabled={!canSubmit}
                onClick={() => mutation.mutate()}
              >
                {mutation.isPending
                  ? t('generateQuiz.generating', 'Génération…')
                  : t('generateQuiz.generate', 'Générer le brouillon')}
              </button>
            </div>
          </>
        )}

        {result && (
          <div>
            <p style={{ color: 'var(--color-success)', fontWeight: 600, marginBottom: 12 }}>
              ✅ {t('generateQuiz.created', 'Brouillon créé : {{count}} question(s).', { count: result.question_count })}
            </p>
            <ul style={{ paddingInlineStart: 18, marginBottom: 16 }}>
              {result.questions.map((q) => (
                <li key={q.order} style={{ fontSize: 13, marginBottom: 4 }}>
                  <span className="status-badge" style={{ marginInlineEnd: 6, textTransform: 'uppercase' }}>
                    {q.source}
                  </span>
                  {q.question_text}
                </li>
              ))}
            </ul>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                {t('app.close', 'Fermer')}
              </button>
              <Link className="btn btn-primary" to="/teacher/quizzes" onClick={onClose}>
                {t('generateQuiz.viewQuizzes', 'Voir mes quiz')}
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
