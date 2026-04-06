import { useId } from 'react';
import { type FieldValues, type Path, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

interface FormTextareaProps<TFieldValues extends FieldValues = FieldValues> {
  name: Path<TFieldValues>;
  label: string;
  rows?: number;
  maxLength?: number;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

function getFieldError(errors: Record<string, unknown>, path: string): string | undefined {
  const resolved = path.split('.').reduce<unknown>(
    (current, part) => (current && typeof current === 'object'
      ? (current as Record<string, unknown>)[part]
      : undefined),
    errors
  );
  if (!resolved || typeof resolved !== 'object') {
    return undefined;
  }

  const message = (resolved as { message?: unknown }).message;
  return typeof message === 'string' ? message : undefined;
}

export function FormTextarea<TFieldValues extends FieldValues = FieldValues>({
  name,
  label,
  rows = 4,
  maxLength,
  placeholder,
  disabled,
  className,
}: FormTextareaProps<TFieldValues>) {
  const fieldId = useId();
  const { t } = useTranslation();
  const {
    register,
    formState: { errors },
  } = useFormContext<TFieldValues>();
  const errorMessage = getFieldError(errors as Record<string, unknown>, String(name));

  return (
    <div className={['form-textarea', className].filter(Boolean).join(' ')}>
      <label className="form-textarea__label" htmlFor={fieldId}>
        {t(label)}
      </label>
      <textarea
        id={fieldId}
        dir="auto"
        rows={rows}
        maxLength={maxLength}
        className="form-textarea__input"
        placeholder={placeholder ? t(placeholder) : undefined}
        disabled={disabled}
        aria-invalid={Boolean(errorMessage)}
        aria-describedby={errorMessage ? `${fieldId}-error` : undefined}
        {...register(name)}
      />
      {errorMessage && (
        <span className="form-textarea__error" id={`${fieldId}-error`} role="alert">
          {t(errorMessage, { defaultValue: errorMessage })}
        </span>
      )}
    </div>
  );
}
