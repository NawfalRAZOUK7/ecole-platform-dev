import { useEffect, useState } from 'react';

export type ThemeMode = 'light' | 'dark';

const STORAGE_KEY = 'ecole-theme';

function getSystemTheme(): ThemeMode {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getInitialTheme(): ThemeMode {
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') {
    return stored;
  }

  return getSystemTheme();
}

export function useTheme() {
  const [theme, setThemeState] = useState<ThemeMode>(() => getInitialTheme());
  const [hasStoredPreference, setHasStoredPreference] = useState(
    () => window.localStorage.getItem(STORAGE_KEY) !== null
  );

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');

    function handleChange() {
      if (!hasStoredPreference) {
        setThemeState(getSystemTheme());
      }
    }

    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, [hasStoredPreference]);

  function setTheme(nextTheme: ThemeMode) {
    setThemeState(nextTheme);
    setHasStoredPreference(true);
    window.localStorage.setItem(STORAGE_KEY, nextTheme);
  }

  function toggleTheme() {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  }

  return {
    theme,
    toggleTheme,
    setTheme,
  };
}
