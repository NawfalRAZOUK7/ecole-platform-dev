/**
 * Brand intro / splash — a short (~1.5s) animated logo reveal shown on app load.
 *
 * The white ring draws in, the graduation cap scales/fades, and the amber bead
 * sweeps along the ring into place — then the whole overlay fades out. Honors
 * prefers-reduced-motion (static logo, quick fade). Mounted once at the app root;
 * it shows again on a full page reload, which is the intended "intro" behaviour.
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useReducedMotion } from '@/shared/hooks/useReducedMotion';

const EASE = [0.16, 1, 0.3, 1] as const;

export function BrandSplash() {
  const reduced = useReducedMotion();
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timeout = setTimeout(() => setVisible(false), reduced ? 600 : 1700);
    return () => clearTimeout(timeout);
  }, [reduced]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="brand-splash"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.45, ease: EASE }}
          aria-hidden="true"
        >
          <motion.svg
            className="brand-splash__mark"
            width="148"
            height="148"
            viewBox="0 0 512 512"
            initial={reduced ? false : { scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, ease: EASE }}
          >
            <defs>
              <linearGradient id="bs-bg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#2563eb" />
                <stop offset="0.55" stopColor="#5b5bef" />
                <stop offset="1" stopColor="#8b5cf6" />
              </linearGradient>
            </defs>
            <rect x="16" y="16" width="480" height="480" rx="116" fill="url(#bs-bg)" />

            {/* ring draws in */}
            <motion.circle
              cx="256"
              cy="248"
              r="170"
              fill="none"
              stroke="#ffffff"
              strokeOpacity="0.35"
              strokeWidth="6"
              strokeLinecap="round"
              initial={reduced ? { pathLength: 1 } : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.9, ease: EASE }}
            />

            {/* graduation cap scales + fades */}
            <motion.g
              fill="#ffffff"
              style={{ transformOrigin: '256px 236px' }}
              initial={reduced ? false : { scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, ease: EASE, delay: 0.25 }}
            >
              <path d="M256 150 L402 214 L256 278 L110 214 Z" />
              <path d="M222 266 L290 266 L290 292 Q290 322 256 322 Q222 322 222 292 Z" />
              <circle cx="256" cy="214" r="12" />
            </motion.g>

            {/* tassel + amber bead sweep along the ring */}
            <motion.g
              style={{ transformOrigin: '256px 248px' }}
              initial={reduced ? false : { rotate: -110, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              transition={{ duration: 0.9, ease: EASE, delay: 0.4 }}
            >
              <path
                d="M402 214 L402 300"
                stroke="#ffffff"
                strokeWidth="7"
                strokeLinecap="round"
                fill="none"
              />
              <circle cx="402" cy="316" r="14" fill="#f59e0b" />
            </motion.g>
          </motion.svg>

          <motion.div
            className="brand-splash__word"
            initial={reduced ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: EASE, delay: 0.55 }}
          >
            École<span>Platform</span>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
