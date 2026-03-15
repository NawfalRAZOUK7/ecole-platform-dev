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
    <div style={{ display: 'flex', gap: '4px' }}>
      {SUPPORTED_LANGUAGES.map((lang) => (
        <button
          key={lang}
          onClick={() => handleChange(lang)}
          style={{
            padding: '4px 10px',
            borderRadius: '4px',
            border: '1px solid #d1d5db',
            background: i18n.language === lang ? '#2563eb' : 'transparent',
            color: i18n.language === lang ? '#fff' : '#374151',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: i18n.language === lang ? 600 : 400,
          }}
        >
          {LANGUAGE_LABELS[lang]}
        </button>
      ))}
    </div>
  );
}
