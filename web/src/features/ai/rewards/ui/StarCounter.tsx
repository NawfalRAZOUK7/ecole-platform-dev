import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { space } from '@/shared/ui/tokens';

interface StarCounterProps {
  value: number;
}

export function StarCounter({ value }: StarCounterProps) {
  const { t } = useTranslation();
  const [displayValue, setDisplayValue] = useState(0);
  const previousValueRef = useRef(0);

  useEffect(() => {
    const startValue = previousValueRef.current;
    const targetValue = Math.max(0, value);
    const durationMs = 700;
    let frameId = 0;
    let startTime = 0;

    function animate(timestamp: number) {
      if (!startTime) {
        startTime = timestamp;
      }

      const progress = Math.min(1, (timestamp - startTime) / durationMs);
      const eased = 1 - (1 - progress) ** 3;
      const nextValue = Math.round(startValue + (targetValue - startValue) * eased);
      setDisplayValue(nextValue);

      if (progress < 1) {
        frameId = window.requestAnimationFrame(animate);
        return;
      }

      previousValueRef.current = targetValue;
    }

    frameId = window.requestAnimationFrame(animate);

    return () => {
      window.cancelAnimationFrame(frameId);
      previousValueRef.current = targetValue;
    };
  }, [value]);

  return (
    <section className="card" style={{ padding: 20, display: 'grid', gap: space.sm }}>
      <span style={{ fontSize: 28, color: 'var(--kids-star-gold)' }} aria-hidden="true">
        ⭐
      </span>
      <strong style={{ fontSize: 32, lineHeight: 1, color: 'var(--kids-star-gold)' }}>
        {displayValue.toLocaleString()}
      </strong>
      <span style={{ color: 'var(--color-text-secondary)' }}>{t('rewards.stats.stars')}</span>
    </section>
  );
}
