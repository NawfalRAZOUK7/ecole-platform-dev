import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  debounceMs?: number;
}

export function SearchInput({
  value,
  onChange,
  placeholder,
  debounceMs = 300,
}: SearchInputProps) {
  const { t } = useTranslation();
  const [internalValue, setInternalValue] = useState(value);

  useEffect(() => {
    setInternalValue(value);
  }, [value]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      if (internalValue !== value) {
        onChange(internalValue);
      }
    }, debounceMs);

    return () => window.clearTimeout(timeout);
  }, [debounceMs, internalValue, onChange, value]);

  return (
    <div className="search-input">
      <input
        type="search"
        className="search-input__field"
        value={internalValue}
        onChange={(event) => setInternalValue(event.target.value)}
        placeholder={t(placeholder)}
        aria-label={t(placeholder)}
      />
      {internalValue && (
        <button
          type="button"
          className="search-input__clear"
          onClick={() => {
            setInternalValue('');
            onChange('');
          }}
          aria-label={t('app.clear', { defaultValue: 'Clear search' })}
        >
          ×
        </button>
      )}
    </div>
  );
}
