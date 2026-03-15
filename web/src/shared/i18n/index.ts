/**
 * i18n configuration — fr (default), ar, en.
 *
 * Reference: S-084 — i18n with RTL support
 * - French default, Arabic with RTL layout
 * - Africa/Casablanca timezone for date formatting
 * - Language switcher updates Accept-Language header on API calls
 */

import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import fr from './locales/fr.json';
import ar from './locales/ar.json';
import en from './locales/en.json';

export const RTL_LANGUAGES = ['ar'];
export const SUPPORTED_LANGUAGES = ['fr', 'ar', 'en'] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

export const LANGUAGE_LABELS: Record<SupportedLanguage, string> = {
  fr: 'Francais',
  ar: 'العربية',
  en: 'English',
};

i18next
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: fr },
      ar: { translation: ar },
      en: { translation: en },
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
  });

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
  options?: Intl.DateTimeFormatOptions
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
