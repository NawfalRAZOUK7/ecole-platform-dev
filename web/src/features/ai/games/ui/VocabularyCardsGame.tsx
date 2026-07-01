import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { GameConfig, VocabularyCardsConfig } from '../model/types';
import { useCompleteGameConfig } from '../model/useGames';
import { GameCompleteBanner } from './GameCompleteBanner';

interface VocabularyCardsGameProps {
  game: GameConfig;
  onExit: () => void;
}

export function VocabularyCardsGame({ game, onExit }: VocabularyCardsGameProps) {
  const { t } = useTranslation();
  const config = game.config as unknown as VocabularyCardsConfig;
  const cards = config.cards ?? [];

  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [startedAt] = useState(() => Date.now());
  const completeMutation = useCompleteGameConfig();
  const completionSentRef = useRef(false);

  useEffect(() => {
    if (!completed || completionSentRef.current) return;
    completionSentRef.current = true;
    const elapsedSeconds = Math.floor((Date.now() - startedAt) / 1000);
    completeMutation.mutate({ gameId: game.id, score: 100, timeSeconds: elapsedSeconds });
  }, [completed, completeMutation, game.id, startedAt]);

  if (cards.length === 0) {
    return <p>{t('studentGames.noCards', 'Aucune carte disponible.')}</p>;
  }

  const card = cards[index];

  const handleNext = () => {
    if (index + 1 >= cards.length) {
      setCompleted(true);
      return;
    }
    setFlipped(false);
    setIndex(index + 1);
  };

  const handlePrev = () => {
    if (index === 0) return;
    setFlipped(false);
    setIndex(index - 1);
  };

  const handleReplay = () => {
    completionSentRef.current = false;
    setCompleted(false);
    setIndex(0);
    setFlipped(false);
  };

  return (
    <div>
      <div style={{ marginBottom: 16, color: 'var(--color-text-secondary)' }}>
        {t('vocabulary.progress', 'Carte')} {index + 1} / {cards.length}
      </div>

      <button
        type="button"
        onClick={() => setFlipped((f) => !f)}
        style={{
          perspective: 1200,
          width: '100%',
          maxWidth: 480,
          aspectRatio: '3 / 2',
          padding: 0,
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          margin: '0 auto 24px',
          display: 'block',
        }}
        aria-label={flipped ? 'Retourner à l’arabe' : 'Voir la traduction'}
      >
        <div
          style={{
            position: 'relative',
            width: '100%',
            height: '100%',
            transformStyle: 'preserve-3d',
            transition: 'transform 0.5s',
            transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backfaceVisibility: 'hidden',
              background: 'linear-gradient(135deg, #fef3c7, #fde68a)',
              borderRadius: 20,
              border: '3px solid #f59e0b',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
              padding: 24,
            }}
          >
            {card.image_url ? (
              <img
                src={card.image_url}
                alt={card.word_ar}
                style={{ maxHeight: '50%', objectFit: 'contain' }}
              />
            ) : null}
            <div style={{ fontSize: 48, fontWeight: 700, color: 'var(--color-text)' }} dir="rtl">
              {card.word_ar}
            </div>
            <div style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>
              {t('vocabulary.tapFlip', 'Clique pour retourner')}
            </div>
          </div>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backfaceVisibility: 'hidden',
              transform: 'rotateY(180deg)',
              background: 'linear-gradient(135deg, #dbeafe, #bfdbfe)',
              borderRadius: 20,
              border: '3px solid #3b82f6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 24,
            }}
          >
            <div style={{ fontSize: 42, fontWeight: 700, color: 'var(--color-text)' }}>
              {card.word_fr}
            </div>
          </div>
        </div>
      </button>

      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handlePrev}
          disabled={index === 0}
        >
          ← {t('app.previous', 'Précédent')}
        </button>
        <button type="button" className="btn btn-primary" onClick={handleNext}>
          {index + 1 >= cards.length
            ? t('vocabulary.finish', 'Terminer')
            : t('app.next', 'Suivant')}{' '}
          →
        </button>
      </div>

      {completed && (
        <GameCompleteBanner
          success
          starsEarned={game.rewardStars}
          xpEarned={game.rewardXp}
          onReplay={handleReplay}
          onExit={onExit}
          loading={completeMutation.isPending}
        />
      )}
    </div>
  );
}
