/**
 * Hidden, document-wide SVG gradient defs for recharts.
 *
 * Mounted once at the app root. Charts reference these by id, e.g.
 * `<Bar fill="url(#chart-grad-primary)" />`. Browsers resolve `url(#id)`
 * document-wide, so one set of defs serves every chart and stays theme-aware
 * (the stops use CSS color variables, so they adapt to light/dark).
 */

const TOKENS = ['primary', 'secondary', 'accent', 'success', 'info'] as const;

export function ChartGradients() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true" focusable="false">
      <defs>
        {TOKENS.map((token) => (
          <linearGradient key={token} id={`chart-grad-${token}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={`var(--color-${token})`} stopOpacity={0.95} />
            <stop offset="100%" stopColor={`var(--color-${token})`} stopOpacity={0.4} />
          </linearGradient>
        ))}
      </defs>
    </svg>
  );
}
