/**
 * Writing Workspace — student writes text and gets AI feedback.
 *
 * Phase A2 — UI shell for the writing assistance feature.
 * Calls POST /api/v1/writing-attempts via writing.service.ts.
 *
 * The AI provider (mock or real Claude) handles the actual feedback generation.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAgeTheme } from '@/shared/hooks/useAgeTheme';
import { useSubmitWriting } from './useWriting';
import type { WritingAttemptResponse } from './writing.service';

const WRITING_TYPES = ['story', 'essay', 'letter', 'description', 'free'] as const;
const MIN_CHARS = 20;
const MAX_CHARS = 5000;

export function WritingWorkspacePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const ageTier = useAgeTheme();
  const submitMutation = useSubmitWriting();

  const [text, setText] = useState('');
  const [writingType, setWritingType] = useState<string>('free');
  const [result, setResult] = useState<WritingAttemptResponse | null>(null);

  const charCount = text.length;
  const canSubmit = charCount >= MIN_CHARS && charCount <= MAX_CHARS && !submitMutation.isPending;

  async function handleSubmit() {
    if (!canSubmit) return;
    try {
      const response = await submitMutation.mutateAsync({
        text,
        language: 'ar',
        writing_type: writingType,
      });
      setResult(response);
    } catch {
      // Error handled by mutation state
    }
  }

  function handleReset() {
    setText('');
    setResult(null);
    submitMutation.reset();
  }

  const isYoung = ageTier === 'maternelle';

  return (
    <div className="page">
      <h1 className="page-title">
        {isYoung ? '✏️ ' : ''}
        {t('writing.title', 'Writing workspace')}
      </h1>
      <p className="page-subtitle">
        {t('writing.subtitle', 'Write your text below and get helpful feedback!')}
      </p>

      {!result ? (
        <div className="card" style={{ padding: 24 }}>
          {/* Writing type selector */}
          <div style={{ marginBottom: 16 }}>
            <label
              htmlFor="writing-type"
              style={{
                display: 'block',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
                marginBottom: 6,
              }}
            >
              {t('writing.typeLabel', 'What are you writing?')}
            </label>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {WRITING_TYPES.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setWritingType(type)}
                  style={{
                    padding: isYoung ? '10px 18px' : '6px 14px',
                    borderRadius: isYoung ? 16 : 10,
                    border:
                      writingType === type
                        ? '2px solid var(--color-primary)'
                        : '2px solid var(--color-border)',
                    background:
                      writingType === type
                        ? 'var(--color-surface-primary, #f3e8ff)'
                        : 'var(--color-surface)',
                    color: writingType === type ? 'var(--color-primary)' : 'var(--color-text)',
                    fontSize: isYoung ? '1rem' : '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {t(`writing.types.${type}`, type)}
                </button>
              ))}
            </div>
          </div>

          {/* Text area */}
          <textarea
            id="writing-textarea"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={t('writing.placeholder', 'Start writing here...')}
            maxLength={MAX_CHARS}
            style={{
              width: '100%',
              minHeight: isYoung ? 250 : 200,
              padding: 16,
              borderRadius: isYoung ? 18 : 12,
              border: '2px solid var(--color-border)',
              fontFamily: 'inherit',
              fontSize: isYoung ? '1.15rem' : '1rem',
              lineHeight: 1.7,
              resize: 'vertical',
              outline: 'none',
              background: 'var(--color-surface)',
              color: 'var(--color-text)',
              direction: 'rtl',
            }}
          />

          {/* Character count + submit */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: 12,
            }}
          >
            <span
              style={{
                fontSize: '0.8rem',
                color:
                  charCount < MIN_CHARS ? 'var(--color-warning)' : 'var(--color-text-secondary)',
              }}
            >
              {charCount} / {MAX_CHARS}{' '}
              {charCount < MIN_CHARS &&
                t('writing.minChars', {
                  count: MIN_CHARS - charCount,
                  defaultValue: `(${MIN_CHARS - charCount} more needed)`,
                })}
            </span>
            <button
              type="button"
              className="kids-cta-btn kids-cta-btn--primary"
              onClick={handleSubmit}
              disabled={!canSubmit}
              style={{
                opacity: canSubmit ? 1 : 0.5,
                cursor: canSubmit ? 'pointer' : 'not-allowed',
                flex: 'none',
                padding: isYoung ? '12px 28px' : '10px 22px',
              }}
            >
              {submitMutation.isPending ? (
                <>{t('writing.checking', 'Checking...')}</>
              ) : (
                <>
                  <span className="kids-cta-btn__icon">🔍</span>
                  {t('writing.submit', 'Check my writing')}
                </>
              )}
            </button>
          </div>

          {submitMutation.isError && (
            <div
              style={{
                marginTop: 12,
                padding: 12,
                background: 'var(--color-surface-error, #fef2f2)',
                borderRadius: 10,
                fontSize: '0.85rem',
                color: 'var(--color-error)',
              }}
            >
              {t('writing.error', 'Something went wrong. Please try again.')}
            </div>
          )}
        </div>
      ) : (
        /* Results view */
        <WritingResult
          result={result}
          originalText={text}
          isYoung={isYoung}
          onTryAgain={handleReset}
          onGoHome={() => navigate('/student/home')}
        />
      )}
    </div>
  );
}

function WritingResult({
  result,
  originalText,
  isYoung,
  onTryAgain,
  onGoHome,
}: {
  result: WritingAttemptResponse;
  originalText: string;
  isYoung: boolean;
  onTryAgain: () => void;
  onGoHome: () => void;
}) {
  const { t } = useTranslation();
  const feedback = result.feedback;

  return (
    <div>
      {/* Encouragement banner */}
      <div
        className="card"
        style={{
          padding: isYoung ? 24 : 20,
          marginBottom: 16,
          background: 'var(--color-surface-success, #ecfdf5)',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: isYoung ? '3rem' : '2rem', marginBottom: 8 }}>
          {feedback.score && feedback.score >= 80
            ? '🎉'
            : feedback.score && feedback.score >= 50
              ? '👍'
              : '💪'}
        </div>
        <p
          style={{
            fontSize: isYoung ? '1.2rem' : '1rem',
            fontWeight: 700,
            color: 'var(--color-success)',
            margin: '0 0 4px',
          }}
        >
          {feedback.encouragement || t('writing.greatJob', 'Great job!')}
        </p>
        {feedback.score !== null && (
          <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', margin: 0 }}>
            {t('writing.score', {
              score: feedback.score,
              defaultValue: `Score: ${feedback.score}/100`,
            })}
          </p>
        )}
      </div>

      {/* Corrected text */}
      {feedback.corrected_text && feedback.corrected_text !== originalText && (
        <div className="card" style={{ padding: 20, marginBottom: 16 }}>
          <h3
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              margin: '0 0 12px',
              color: 'var(--color-primary)',
            }}
          >
            {t('writing.correctedVersion', 'Corrected version')}
          </h3>
          <div
            style={{
              padding: 14,
              background: 'var(--color-bg-secondary, #f9fafb)',
              borderRadius: 10,
              fontSize: isYoung ? '1.1rem' : '0.95rem',
              lineHeight: 1.7,
              direction: 'rtl',
              whiteSpace: 'pre-wrap',
            }}
          >
            {feedback.corrected_text}
          </div>
        </div>
      )}

      {/* Suggestions */}
      {feedback.suggestions.length > 0 && (
        <div className="card" style={{ padding: 20, marginBottom: 16 }}>
          <h3
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              margin: '0 0 12px',
              color: 'var(--color-primary)',
            }}
          >
            {t('writing.suggestions', 'Tips to improve')}
          </h3>
          <ul style={{ margin: 0, paddingInlineStart: 20 }}>
            {feedback.suggestions.map((suggestion, index) => (
              <li
                key={index}
                style={{
                  fontSize: isYoung ? '1rem' : '0.9rem',
                  marginBottom: 8,
                  lineHeight: 1.5,
                  color: 'var(--color-text)',
                }}
              >
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <button
          type="button"
          className="kids-cta-btn kids-cta-btn--writing"
          onClick={onTryAgain}
          style={{ flex: '1 1 160px' }}
        >
          <span className="kids-cta-btn__icon">✏️</span>
          {t('writing.tryAgain', 'Write again')}
        </button>
        <button
          type="button"
          className="kids-cta-btn kids-cta-btn--secondary"
          onClick={onGoHome}
          style={{ flex: '1 1 160px' }}
        >
          <span className="kids-cta-btn__icon">🏠</span>
          {t('writing.goHome', 'Back home')}
        </button>
      </div>
    </div>
  );
}
