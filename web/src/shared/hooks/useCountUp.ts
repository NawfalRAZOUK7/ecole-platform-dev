/**
 * Animated number count-up.
 *
 * Eases from 0 (or the previous value) to `target` over `duration` ms using
 * requestAnimationFrame. Respects prefers-reduced-motion (returns the target
 * immediately) and cleans up its animation frame on unmount / target change.
 */

import { useEffect, useRef, useState } from 'react';
import { useReducedMotion } from '@/shared/hooks/useReducedMotion';

interface UseCountUpOptions {
  duration?: number;
  /** Animate from this value instead of 0 on first run. */
  from?: number;
}

// easeOutCubic — matches the app's "emphasized" motion curve.
const easeOutCubic = (t: number): number => 1 - Math.pow(1 - t, 3);

export function useCountUp(target: number, options: UseCountUpOptions = {}): number {
  const { duration = 800, from = 0 } = options;
  const reducedMotion = useReducedMotion();
  const [display, setDisplay] = useState(reducedMotion ? target : from);
  const frameRef = useRef<number | null>(null);
  const startValueRef = useRef(from);

  useEffect(() => {
    if (reducedMotion || duration <= 0 || !Number.isFinite(target)) {
      setDisplay(target);
      return;
    }

    const startValue = startValueRef.current;
    const delta = target - startValue;
    if (delta === 0) {
      setDisplay(target);
      return;
    }

    let startTime: number | null = null;

    const tick = (now: number) => {
      if (startTime === null) startTime = now;
      const progress = Math.min((now - startTime) / duration, 1);
      const next = startValue + delta * easeOutCubic(progress);
      setDisplay(next);
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      } else {
        startValueRef.current = target;
      }
    };

    frameRef.current = requestAnimationFrame(tick);

    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      startValueRef.current = target;
    };
  }, [target, duration, reducedMotion]);

  return display;
}
