/**
 * Language switcher component — toggles between fr, ar, en.
 *
 * Reference: S-084 — i18n with RTL support
 * Updates i18n language and document direction (RTL for Arabic).
 * ar/en are lazy-loaded on first switch; subsequent switches are instant.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  SUPPORTED_LANGUAGES,
  LANGUAGE_LABELS,
  applyDirection,
  loadLanguage,
  type SupportedLanguage,
} from '@/shared/i18n';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [loadingLang, setLoadingLang] = useState<SupportedLanguage | null>(null);

  async function handleChange(lang: SupportedLanguage) {
    if (i18n.language === lang || loadingLang !== null) return;
    setLoadingLang(lang);
    try {
      await loadLanguage(lang);
      await i18n.changeLanguage(lang);
      applyDirection(lang);
    } finally {
      setLoadingLang(null);
    }
  }

  return (
    <div className="language-switcher">
      {SUPPORTED_LANGUAGES.map((lang) => (
        <button
          key={lang}
          type="button"
          onClick={() => void handleChange(lang)}
          className={`language-switcher__button ${i18n.language === lang ? 'language-switcher__button--active' : ''}`}
          aria-pressed={i18n.language === lang}
          disabled={loadingLang === lang}
          aria-busy={loadingLang === lang}
        >
          {loadingLang === lang ? '…' : LANGUAGE_LABELS[lang]}
        </button>
      ))}
    </div>
  );
}
