/**
 * Tests for src/shared/i18n/index.ts
 */
import { describe, it, expect } from 'vitest';
import {
  RTL_LANGUAGES,
  SUPPORTED_LANGUAGES,
  LANGUAGE_LABELS,
  applyDirection,
  formatDate,
  formatCurrency,
  loadLanguage,
} from '@/shared/i18n';

describe('i18n constants', () => {
  it('RTL_LANGUAGES contains ar', () => {
    expect(RTL_LANGUAGES).toContain('ar');
  });

  it('SUPPORTED_LANGUAGES contains fr, ar, en', () => {
    expect(SUPPORTED_LANGUAGES).toContain('fr');
    expect(SUPPORTED_LANGUAGES).toContain('ar');
    expect(SUPPORTED_LANGUAGES).toContain('en');
  });

  it('LANGUAGE_LABELS has labels for each language', () => {
    expect(LANGUAGE_LABELS.fr).toBeTruthy();
    expect(LANGUAGE_LABELS.ar).toBeTruthy();
    expect(LANGUAGE_LABELS.en).toBeTruthy();
  });
});

describe('applyDirection', () => {
  it('sets dir=rtl and lang=ar for Arabic', () => {
    applyDirection('ar');
    expect(document.documentElement.getAttribute('dir')).toBe('rtl');
    expect(document.documentElement.getAttribute('lang')).toBe('ar');
  });

  it('sets dir=ltr and lang=fr for French', () => {
    applyDirection('fr');
    expect(document.documentElement.getAttribute('dir')).toBe('ltr');
    expect(document.documentElement.getAttribute('lang')).toBe('fr');
  });

  it('sets dir=ltr and lang=en for English', () => {
    applyDirection('en');
    expect(document.documentElement.getAttribute('dir')).toBe('ltr');
    expect(document.documentElement.getAttribute('lang')).toBe('en');
  });
});

describe('formatDate', () => {
  it('returns "-" for null/undefined input', () => {
    expect(formatDate(null)).toBe('-');
    expect(formatDate(undefined)).toBe('-');
  });

  it('formats a date string', () => {
    const result = formatDate('2026-01-15', 'fr');
    expect(result).toBeTruthy();
    expect(result).not.toBe('-');
    // Should contain year 2026
    expect(result).toContain('2026');
  });

  it('formats a Date object', () => {
    const date = new Date('2026-06-01T00:00:00Z');
    const result = formatDate(date, 'fr');
    expect(result).toBeTruthy();
    expect(result).not.toBe('-');
  });

  it('handles invalid date string gracefully', () => {
    const result = formatDate('not-a-date');
    // Falls back to string representation on error
    expect(result).toBeTruthy();
  });

  it('accepts custom options', () => {
    const result = formatDate('2026-01-15', 'fr', { year: 'numeric' });
    expect(result).toContain('2026');
  });

  it('formats with dateStyle option', () => {
    const result = formatDate('2026-01-15', 'en', { dateStyle: 'short' });
    expect(result).toBeTruthy();
  });
});

describe('formatCurrency', () => {
  it('formats amount with default MAD currency', () => {
    const result = formatCurrency(1000);
    expect(result).toBeTruthy();
    expect(result).toContain('1');
  });

  it('formats amount with EUR currency', () => {
    const result = formatCurrency(500, 'EUR');
    expect(result).toBeTruthy();
  });

  it('formats zero correctly', () => {
    const result = formatCurrency(0);
    expect(result).toBeTruthy();
  });
});

describe('loadLanguage', () => {
  it('is a no-op for already-loaded language (fr)', async () => {
    // Should not throw
    await expect(loadLanguage('fr')).resolves.toBeUndefined();
  });

  it('loads English language', async () => {
    await expect(loadLanguage('en')).resolves.toBeUndefined();
  });

  it('loads Arabic language', async () => {
    await expect(loadLanguage('ar')).resolves.toBeUndefined();
  });

  it('handles unknown language gracefully', async () => {
    await expect(loadLanguage('xx')).resolves.toBeUndefined();
  });
});
