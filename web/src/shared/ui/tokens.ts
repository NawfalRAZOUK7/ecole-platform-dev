/**
 * Design tokens — JavaScript/TypeScript constants.
 *
 * These mirror the CSS custom properties in styles.css and the mobile
 * AppSpacing / AppRadii / AppTypography / AppColors token files.
 * Use CSS variables (var(--space-*)) in style props wherever possible.
 * Use these JS constants when you need numeric values for calculations.
 */

// ── Colors ──

/** Core brand colors */
export const colors = {
  primary: '#2563eb',
  primaryLight: '#60a5fa',
  primaryDark: '#1d4ed8',
  primaryHover: '#1d4ed8',
  secondary: '#8b5cf6',
  accent: '#f59e0b',
  danger: '#ef4444',
  dangerHover: '#dc2626',
  error: '#ef4444',
  success: '#10b981',
  warning: '#f59e0b',
  info: '#0ea5e9',
} as const;

/** Surface & background colors — light mode */
export const light = {
  bg: '#f9fafb',
  surface: '#ffffff',
  text: '#111827',
  textSecondary: '#6b7280',
  inverseText: '#f8fafc',
  border: '#e5e7eb',
} as const;

/** Surface & background colors — dark mode */
export const dark = {
  bg: '#0f172a',
  surface: '#1e293b',
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  inverseText: '#0f172a',
  border: '#334155',
} as const;

/** Kids theme colors */
export const kids = {
  primary: '#7c3aed',
  bg: '#fff7ed',
  bgSecondary: '#fef3c7',
  text: '#1f1035',
  textSecondary: '#6d5a8a',
  border: '#e9d5ff',
  sidebarBg: '#5b21b6',
  sidebarText: '#ffffff',
} as const;

/** Chart colors for data visualization */
export const chart = {
  1: colors.primary,
  2: colors.success,
  3: colors.accent,
  4: colors.secondary,
  5: colors.info,
  6: colors.error,
} as const;

/** CSS var() shorthands for colors in inline style props */
export const colorVars = {
  primary: 'var(--color-primary)',
  primaryLight: 'var(--color-primary-light)',
  primaryDark: 'var(--color-primary-dark)',
  secondary: 'var(--color-secondary)',
  accent: 'var(--color-accent)',
  danger: 'var(--color-danger)',
  success: 'var(--color-success)',
  warning: 'var(--color-warning)',
  info: 'var(--color-info)',
  bg: 'var(--color-bg)',
  surface: 'var(--color-surface)',
  text: 'var(--color-text)',
  textSecondary: 'var(--color-text-secondary)',
  border: 'var(--color-border)',
} as const;

// ── Shadows ──

/** Shadow scale — matches CSS custom properties */
export const shadows = {
  sm: 'var(--shadow-sm)',
  md: 'var(--shadow-md)',
  lg: 'var(--shadow-lg)',
  xl: 'var(--shadow-xl)',
  glowPrimary: 'var(--shadow-glow-primary)',
} as const;

/** Shadow values for JS calculations */
export const shadowValues = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
} as const;

// ── Typography ──

/** Font family */
export const fontFamily = "'Cairo', sans-serif" as const;

/** Font sizes in px */
export const fontSize = {
  xs: 12,
  sm: 14,
  base: 16,
  md: 18,
  lg: 20,
  xl: 24,
  '2xl': 28,
} as const;

/** Font weights */
export const fontWeight = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

/** Line heights */
export const lineHeight = {
  tight: 1.25,
  normal: 1.5,
  relaxed: 1.625,
} as const;

// ── Spacing ──

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

// ── Z-Index Scale ──

export const zIndex = {
  base: 0,
  dropdown: 100,
  sticky: 200,
  modal: 300,
  toast: 400,
  tooltip: 500,
} as const;

// ── Breakpoints ──

export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const;

// ── Transitions ──

export const transitions = {
  fast: '0.1s ease',
  normal: '0.15s ease',
  slow: '0.25s ease',
  bounce: '0.3s cubic-bezier(0.16, 1, 0.3, 1)',
} as const;
