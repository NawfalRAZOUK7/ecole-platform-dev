import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { GameConfig, MemoryMatchConfig, MemoryMatchPair } from '../model/types';
import { useCompleteGameConfig } from '../model/useGames';
import { GameCompleteBanner } from './GameCompleteBanner';

interface MemoryMatchGameProps {
  game: GameConfig;
  onExit: () => void;
}

interface Card {
  key: string;
  pairId: number;
  face: 'front' | 'back';
  text: string;
  imageUrl?: string | null;
}

function buildDeck(pairs: MemoryMatchPair[]): Card[] {
  const deck: Card[] = [];
  pairs.forEach((pair, index) => {
    deck.push({
      key: `p${index}-front`,
      pairId: index,
      face: 'front',
      text: pair.front,
      imageUrl: pair.image_url ?? null,
    });
    deck.push({
      key: `p${index}-back`,
      pairId: index,
      face: 'back',
      text: pair.back,
      imageUrl: pair.image_url ?? null,
    });
  });
  // Fisher-Yates shuffle
  for (let i = deck.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  return deck;
}

export function MemoryMatchGame({ game, onExit }: MemoryMatchGameProps) {
  const { t } = useTranslation();
  const config = game.config as unknown as MemoryMatchConfig;
  const pairs = useMemo(() => config.pairs ?? [], [config.pairs]);
  const gridCols = config.grid_cols || 4;
  const timeLimit = config.time_limit || 60;

  const [deck, setDeck] = useState<Card[]>(() => buildDeck(pairs));
  const [flipped, setFlipped] = useState<number[]>([]);
  const [matched, setMatched] = useState<Set<number>>(new Set());
  const [moves, setMoves] = useState(0);
  const [timeLeft, setTimeLeft] = useState(timeLimit);
  const [completed, setCompleted] = useState(false);
  const [startedAt] = useState(() => Date.now());
  const completeMutation = useCompleteGameConfig();
  const completionSentRef = useRef(false);

  useEffect(() => {
    setDeck(buildDeck(pairs));
  }, [pairs]);

  useEffect(() => {
    if (completed || timeLeft <= 0) return;
    const timer = window.setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [completed, timeLeft]);

  useEffect(() => {
    if (matched.size === pairs.length && pairs.length > 0 && !completed) {
      setCompleted(true);
    }
  }, [matched, pairs.length, completed]);

  useEffect(() => {
    if (!completed || completionSentRef.current) return;
    completionSentRef.current = true;
    const elapsedSeconds = Math.floor((Date.now() - startedAt) / 1000);
    const score = Math.max(0, Math.round((pairs.length / Math.max(moves, pairs.length)) * 100));
    completeMutation.mutate({ gameId: game.id, score, timeSeconds: elapsedSeconds });
  }, [completed, completeMutation, game.id, moves, pairs.length, startedAt]);

  const handleFlip = useCallback(
    (index: number) => {
      if (completed || timeLeft <= 0) return;
      if (flipped.includes(index)) return;
      if (matched.has(deck[index].pairId)) return;
      if (flipped.length === 2) return;

      const next = [...flipped, index];
      setFlipped(next);

      if (next.length === 2) {
        setMoves((m) => m + 1);
        const [a, b] = next;
        if (deck[a].pairId === deck[b].pairId && deck[a].face !== deck[b].face) {
          window.setTimeout(() => {
            setMatched((prev) => new Set(prev).add(deck[a].pairId));
            setFlipped([]);
          }, 500);
        } else {
          window.setTimeout(() => setFlipped([]), 900);
        }
      }
    },
    [completed, deck, flipped, matched, timeLeft],
  );

  const handleReplay = () => {
    completionSentRef.current = false;
    setDeck(buildDeck(pairs));
    setFlipped([]);
    setMatched(new Set());
    setMoves(0);
    setTimeLeft(timeLimit);
    setCompleted(false);
  };

  const timedOut = !completed && timeLeft <= 0;

  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: 16,
          flexWrap: 'wrap',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <StatChip icon="⏱️" label={`${timeLeft}s`} />
        <StatChip
          icon="🎯"
          label={t('memoryMatch.moves', { count: moves, defaultValue: '{{count}} coups' })}
        />
        <StatChip icon="✅" label={`${matched.size} / ${pairs.length}`} />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${gridCols}, minmax(80px, 1fr))`,
          gap: 12,
          maxWidth: 640,
        }}
      >
        {deck.map((card, index) => {
          const isFlipped = flipped.includes(index) || matched.has(card.pairId);
          return (
            <MemoryCard
              key={card.key}
              card={card}
              flipped={isFlipped}
              onClick={() => handleFlip(index)}
            />
          );
        })}
      </div>

      {(completed || timedOut) && (
        <GameCompleteBanner
          success={completed}
          starsEarned={completed ? game.rewardStars : 0}
          xpEarned={completed ? game.rewardXp : 0}
          onReplay={handleReplay}
          onExit={onExit}
          loading={completeMutation.isPending}
        />
      )}
    </div>
  );
}

function MemoryCard({
  card,
  flipped,
  onClick,
}: {
  card: Card;
  flipped: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={flipped}
      style={{
        perspective: 1000,
        aspectRatio: '3 / 4',
        border: 'none',
        background: 'transparent',
        cursor: flipped ? 'default' : 'pointer',
        padding: 0,
      }}
      aria-label={flipped ? card.text : 'Carte face cachée'}
    >
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          transformStyle: 'preserve-3d',
          transition: 'transform 0.4s',
          transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 16,
            backfaceVisibility: 'hidden',
            background: 'linear-gradient(135deg, #7c3aed, #5b21b6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 32,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}
        >
          ?
        </div>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 16,
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
            background: '#fff',
            border: '2px solid var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 8,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}
        >
          {card.face === 'back' && card.imageUrl ? (
            <img
              src={card.imageUrl}
              alt={card.text}
              style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
            />
          ) : (
            <span
              style={{
                fontSize: 20,
                fontWeight: 700,
                textAlign: 'center',
                color: 'var(--color-text)',
              }}
            >
              {card.text}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

function StatChip({ icon, label }: { icon: string; label: string }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '6px 14px',
        borderRadius: 999,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        fontSize: 14,
      }}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </span>
  );
}
