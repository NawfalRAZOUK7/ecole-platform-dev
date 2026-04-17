/**
 * Design tokens — JavaScript/TypeScript constants.
 *
 * These mirror the CSS custom properties in styles.css and the mobile
 * AppSpacing / AppRadii / AppTypography token files.
 * Use CSS variables (var(--space-*)) in style props wherever possible.
 * Use these JS constants when you need numeric values for calculations.
 */

/** Spacing scale in px — matches mobile AppSpacing */
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

/** Border-radius scale in px — matches mobile AppRadii */
export const radii = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 999,
} as const;

/** CSS var() shorthands for inline style props */
export const space = {
  xs: 'var(--space-xs)',
  sm: 'var(--space-sm)',
  md: 'var(--space-md)',
  base: 'var(--space-base)',
  lg: 'var(--space-lg)',
  xl: 'var(--space-xl)',
  xxl: 'var(--space-xxl)',
} as const;

export const radius = {
  sm: 'var(--radius-sm)',
  md: 'var(--radius-md)',
  lg: 'var(--radius-lg)',
  xl: 'var(--radius-xl)',
  full: 'var(--radius-full)',
} as const;
