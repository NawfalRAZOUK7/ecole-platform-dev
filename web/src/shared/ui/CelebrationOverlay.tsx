import { useEffect, useState } from 'react';

export type CelebrationTrigger = 'quiz_complete' | 'badge_earned' | 'streak_milestone';

interface Props {
  trigger: CelebrationTrigger | null;
  onDone?: () => void;
}

const CELEBRATION_CONFIG: Record<CelebrationTrigger, { emoji: string; message: string }> = {
  quiz_complete: { emoji: '🎉', message: 'Bravo!' },
  badge_earned: { emoji: '🏅', message: 'Badge débloqué!' },
  streak_milestone: { emoji: '🔥', message: 'Série en cours!' },
};

const CONFETTI_COLORS = ['#7c3aed', '#f59e0b', '#10b981', '#3b82f6', '#ef4444', '#ec4899'];

export function CelebrationOverlay({ trigger, onDone }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!trigger) return;
    setVisible(true);
    const timer = setTimeout(() => {
      setVisible(false);
      onDone?.();
    }, 3000);
    return () => clearTimeout(timer);
  }, [trigger, onDone]);

  if (!visible || !trigger) return null;

  const config = CELEBRATION_CONFIG[trigger];

  return (
    <>
      <ConfettiLayer />
      <div className="celebration-overlay" aria-live="assertive" aria-atomic="true">
        <div className="celebration-overlay__content">
          <span className="celebration-overlay__emoji">{config.emoji}</span>
          <div className="celebration-overlay__message">{config.message}</div>
        </div>
      </div>
    </>
  );
}

function ConfettiLayer() {
  const pieces = Array.from({ length: 40 }, (_, i) => i);

  return (
    <div className="celebration-confetti" aria-hidden="true">
      {pieces.map((i) => {
        const color = CONFETTI_COLORS[i % CONFETTI_COLORS.length];
        const left = `${Math.random() * 100}%`;
        const duration = `${1.5 + Math.random() * 1.5}s`;
        const delay = `${Math.random() * 0.8}s`;
        const size = `${8 + Math.random() * 8}px`;
        const rotation = Math.random() > 0.5 ? 'rotate(45deg)' : 'none';

        return (
          <div
            key={i}
            className="confetti-piece"
            style={{
              left,
              background: color,
              animationDuration: duration,
              animationDelay: delay,
              width: size,
              height: size,
              borderRadius: Math.random() > 0.5 ? '50%' : '2px',
              transform: rotation,
            }}
          />
        );
      })}
    </div>
  );
}
