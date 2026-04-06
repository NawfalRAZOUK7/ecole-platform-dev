import { useId } from 'react';
import { type FieldValues, type Path, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

interface SelectOption {
  value: string;
  label: string;
}

interface FormSelectProps<TFieldValues extends FieldValues = FieldValues> {
  name: Path<TFieldValues>;
  label: string;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

function getError(errors: Record<string, unknown>, path: string): string | undefined {
  const value = path.split('.').reduce<unknown>(
    (current, part) => (current && typeof current === 'object'
      ? (current as Record<string, unknown>)[part]
      : undefined),
    errors
  );
  return typeof value === 'object' && value && typeof (value as { message?: unknown }).message === 'string'
    ? ((value as { message: string }).message)
    : undefined;
}

export function FormSelect<TFieldValues extends FieldValues = FieldValues>({
  name,
  label,
  options,
  placeholder,
  disabled,
  className,
}: FormSelectProps<TFieldValues>) {
  const selectId = useId();
  const { t } = useTranslation();
  const {
    register,
    formState: { errors },
  } = useFormContext<TFieldValues>();
  const errorMessage = getError(errors as Record<string, unknown>, String(name));

  return (
    <div className={['form-select', className].filter(Boolean).join(' ')}>
      <label className="form-select__label" htmlFor={selectId}>
        {t(label)}
      </label>
      <select
        id={selectId}
        dir="auto"
        className="form-select__input"
        disabled={disabled}
        aria-invalid={Boolean(errorMessage)}
        aria-describedby={errorMessage ? `${selectId}-error` : undefined}
        {...register(name)}
      >
        {placeholder && (
          <option value="">
            {t(placeholder)}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {t(option.label)}
          </option>
        ))}
      </select>
      {errorMessage && (
        <span className="form-select__error" id={`${selectId}-error`} role="alert">
          {t(errorMessage, { defaultValue: errorMessage })}
        </span>
      )}
    </div>
  );
}
