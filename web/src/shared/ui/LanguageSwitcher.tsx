/**
 * Language switcher component — toggles between fr, ar, en.
 *
 * Reference: S-084 — i18n with RTL support
 * Updates i18n language and document direction (RTL for Arabic).
 */

import { useTranslation } from 'react-i18next';
import {
  SUPPORTED_LANGUAGES,
  LANGUAGE_LABELS,
  applyDirection,
  type SupportedLanguage,
} from '@/shared/i18n';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();

  function handleChange(lang: SupportedLanguage) {
    i18n.changeLanguage(lang);
    applyDirection(lang);
  }

  return (
    <div className="language-switcher">
      {SUPPORTED_LANGUAGES.map((lang) => (
        <button
          key={lang}
          type="button"
          onClick={() => handleChange(lang)}
          className={`language-switcher__button ${i18n.language === lang ? 'language-switcher__button--active' : ''}`}
          aria-pressed={i18n.language === lang}
        >
          {LANGUAGE_LABELS[lang]}
        </button>
      ))}
    </div>
  );
}
