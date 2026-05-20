import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { GameConfig, SortingConfig } from '../model/types';
import { useCompleteGameConfig } from '../model/useGames';
import { GameCompleteBanner } from './GameCompleteBanner';

interface SortingGameProps {
  game: GameConfig;
  onExit: () => void;
}

interface SortItem {
  id: string;
  label: string;
  category: string;
}

const CATEGORY_COLORS = ['#7c3aed', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#14b8a6'];

export function SortingGame({ game, onExit }: SortingGameProps) {
  const { t } = useTranslation();
  const config = game.config as unknown as SortingConfig;
  const categories = config.categories ?? [];

  const items = useMemo<SortItem[]>(() => {
    const built: SortItem[] = [];
    categories.forEach((cat) => {
      cat.items.forEach((label, i) => {
        built.push({ id: `${cat.name}-${i}-${label}`, label, category: cat.name });
      });
    });
    for (let i = built.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [built[i], built[j]] = [built[j], built[i]];
    }
    return built;
  }, [categories]);

  const [placements, setPlacements] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, 'correct' | 'wrong'>>({});
  const [completed, setCompleted] = useState(false);
  const [startedAt] = useState(() => Date.now());
  const completeMutation = useCompleteGameConfig();
  const completionSentRef = useRef(false);

  const correctCount = Object.entries(placements).filter(
    ([id, cat]) => items.find((it) => it.id === id)?.category === cat,
  ).length;

  useEffect(() => {
    if (!completed && correctCount === items.length && items.length > 0) {
      setCompleted(true);
    }
  }, [correctCount, items.length, completed]);

  useEffect(() => {
    if (!completed || completionSentRef.current) return;
    completionSentRef.current = true;
    const elapsedSeconds = Math.floor((Date.now() - startedAt) / 1000);
    completeMutation.mutate({ gameId: game.id, score: 100, timeSeconds: elapsedSeconds });
  }, [completed, completeMutation, game.id, startedAt]);

  const onDropItem = (itemId: string, category: string) => {
    const item = items.find((it) => it.id === itemId);
    if (!item) return;
    const isCorrect = item.category === category;
    setPlacements((prev) => ({ ...prev, [itemId]: category }));
    setFeedback((prev) => ({ ...prev, [itemId]: isCorrect ? 'correct' : 'wrong' }));
    if (!isCorrect) {
      window.setTimeout(() => {
        setPlacements((prev) => {
          const next = { ...prev };
          delete next[itemId];
          return next;
        });
        setFeedback((prev) => {
          const next = { ...prev };
          delete next[itemId];
          return next;
        });
      }, 700);
    }
  };

  const handleReplay = () => {
    completionSentRef.current = false;
    setPlacements({});
    setFeedback({});
    setCompleted(false);
  };

  const availableItems = items.filter((it) => !placements[it.id] || feedback[it.id] === 'wrong');

  return (
    <div>
      <div style={{ marginBottom: 16, color: 'var(--color-text-secondary)' }}>
        {t('sortingGame.progress', 'Progression :')} {correctCount} / {items.length}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${Math.min(categories.length, 3)}, 1fr)`,
          gap: 16,
          marginBottom: 24,
        }}
      >
        {categories.map((cat, idx) => {
          const color = CATEGORY_COLORS[idx % CATEGORY_COLORS.length];
          const placedItems = items.filter(
            (it) => placements[it.id] === cat.name && feedback[it.id] === 'correct',
          );
          return (
            <div
              key={cat.name}
              onDragOver={(e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
              }}
              onDrop={(e) => {
                e.preventDefault();
                const itemId = e.dataTransfer.getData('text/plain');
                if (itemId) onDropItem(itemId, cat.name);
              }}
              style={{
                padding: 16,
                borderRadius: 12,
                border: `3px dashed ${color}`,
                background: `${color}10`,
                minHeight: 160,
              }}
            >
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 700,
                  color,
                  marginBottom: 12,
                  textAlign: 'center',
                }}
              >
                {cat.name}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {placedItems.map((it) => (
                  <span
                    key={it.id}
                    style={{
                      padding: '6px 12px',
                      borderRadius: 999,
                      background: color,
                      color: '#fff',
                      fontSize: 14,
                      fontWeight: 600,
                    }}
                  >
                    ✓ {it.label}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        {availableItems.map((it) => {
          const fb = feedback[it.id];
          return (
            <div
              key={it.id}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('text/plain', it.id);
                e.dataTransfer.effectAllowed = 'move';
              }}
              style={{
                padding: '10px 16px',
                borderRadius: 10,
                background: 'var(--color-surface)',
                border:
                  fb === 'wrong'
                    ? '2px solid #ef4444'
                    : fb === 'correct'
                      ? '2px solid #10b981'
                      : '2px solid var(--color-border)',
                cursor: 'grab',
                fontWeight: 600,
                animation: fb === 'wrong' ? 'sort-shake 0.5s' : undefined,
              }}
            >
              {it.label}
            </div>
          );
        })}
      </div>

      <style>{`
        @keyframes sort-shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-6px); }
          75% { transform: translateX(6px); }
        }
      `}</style>

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
