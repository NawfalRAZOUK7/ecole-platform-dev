import { useId } from 'react';
import { type FieldValues, type Path, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

interface FormDatePickerProps<TFieldValues extends FieldValues = FieldValues> {
  name: Path<TFieldValues>;
  label: string;
  minDate?: string;
  maxDate?: string;
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
  if (!value || typeof value !== 'object') {
    return undefined;
  }
  const message = (value as { message?: unknown }).message;
  return typeof message === 'string' ? message : undefined;
}

export function FormDatePicker<TFieldValues extends FieldValues = FieldValues>({
  name,
  label,
  minDate,
  maxDate,
  disabled,
  className,
}: FormDatePickerProps<TFieldValues>) {
  const dateId = useId();
  const { t } = useTranslation();
  const {
    register,
    formState: { errors },
  } = useFormContext<TFieldValues>();
  const errorMessage = getError(errors as Record<string, unknown>, String(name));

  return (
    <div className={['form-date', className].filter(Boolean).join(' ')}>
      <label className="form-date__label" htmlFor={dateId}>
        {t(label)}
      </label>
      <input
        id={dateId}
        dir="auto"
        type="date"
        lang="fr-MA"
        min={minDate}
        max={maxDate}
        className="form-date__input"
        disabled={disabled}
        aria-invalid={Boolean(errorMessage)}
        aria-describedby={errorMessage ? `${dateId}-error` : undefined}
        {...register(name)}
      />
      {errorMessage && (
        <span className="form-date__error" id={`${dateId}-error`} role="alert">
          {t(errorMessage, { defaultValue: errorMessage })}
        </span>
      )}
    </div>
  );
}
