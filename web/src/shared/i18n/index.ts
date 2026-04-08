/**
 * i18n configuration — fr (default), ar, en.
 *
 * Reference: S-084 — i18n with RTL support
 * - French default, Arabic with RTL layout
 * - Africa/Casablanca timezone for date formatting
 * - Language switcher updates Accept-Language header on API calls
 * - ar/en are lazy-loaded on demand; only fr is in the initial bundle
 */

import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import fr from './locales/fr.json';

export const RTL_LANGUAGES = ['ar'];
export const SUPPORTED_LANGUAGES = ['fr', 'ar', 'en'] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

export const LANGUAGE_LABELS: Record<SupportedLanguage, string> = {
  fr: 'Francais',
  ar: 'العربية',
  en: 'English',
};

/** Languages whose JSON bundles are already in memory */
const loadedLanguages = new Set<string>(['fr']);

/**
 * Dynamically load a locale bundle.
 * Safe to call multiple times — subsequent calls for a loaded language are no-ops.
 * Falls back to `fr` silently on import failure.
 */
export async function loadLanguage(lang: string): Promise<void> {
  if (loadedLanguages.has(lang)) return;

  try {
    let data: Record<string, unknown>;

    if (lang === 'ar') {
      const m = await import('./locales/ar.json');
      data = m.default as Record<string, unknown>;
    } else if (lang === 'en') {
      const m = await import('./locales/en.json');
      data = m.default as Record<string, unknown>;
    } else {
      return;
    }

    i18next.addResourceBundle(lang, 'translation', data, true, true);
    loadedLanguages.add(lang);
  } catch {
    // Import failed — i18next will fall back to 'fr' via fallbackLng
  }
}

i18next
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: fr },
    },
    fallbackLng: 'fr',
    supportedLngs: ['fr', 'ar', 'en'],
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
    // Tell i18next that not all language bundles are pre-loaded
    partialBundledLanguages: true,
  });

// If the detected/stored language is not fr, load it now so the first
// render shows the correct translations with minimal flicker.
const detectedLang = i18next.language?.split('-')[0] ?? 'fr';
if (detectedLang !== 'fr' && SUPPORTED_LANGUAGES.includes(detectedLang as SupportedLanguage)) {
  void loadLanguage(detectedLang).then(() => {
    void i18next.changeLanguage(detectedLang);
    applyDirection(detectedLang);
  });
}

/** Apply RTL direction to the document based on language */
export function applyDirection(lang: string) {
  const dir = RTL_LANGUAGES.includes(lang) ? 'rtl' : 'ltr';
  document.documentElement.setAttribute('dir', dir);
  document.documentElement.setAttribute('lang', lang);
}

/** Format a date for display using Africa/Casablanca timezone */
export function formatDate(
  dateStr: string | null | undefined,
  lang?: string,
  options?: Intl.DateTimeFormatOptions,
): string {
  if (!dateStr) return '-';
  const locale = lang || i18next.language || 'fr';
  return new Intl.DateTimeFormat(locale, {
    timeZone: 'Africa/Casablanca',
    dateStyle: 'medium',
    ...options,
  }).format(new Date(dateStr));
}

/** Format currency for display */
export function formatCurrency(amount: number, currency = 'MAD'): string {
  return new Intl.NumberFormat(i18next.language || 'fr', {
    style: 'currency',
    currency,
  }).format(amount);
}

// Initialize direction on load
applyDirection(i18next.language || 'fr');

export default i18next;
