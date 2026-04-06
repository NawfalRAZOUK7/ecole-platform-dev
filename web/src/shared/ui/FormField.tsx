import { useId } from 'react';
import { type FieldValues, type Path, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

interface FormFieldProps<TFieldValues extends FieldValues = FieldValues> {
  name: Path<TFieldValues>;
  label: string;
  type?: React.HTMLInputTypeAttribute;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

function resolveErrorMessage(
  errors: Record<string, unknown>,
  path: string
): string | undefined {
  const parts = path.split('.');
  let current: unknown = errors;

  for (const part of parts) {
    if (!current || typeof current !== 'object') {
      return undefined;
    }
    current = (current as Record<string, unknown>)[part];
  }

  if (!current || typeof current !== 'object') {
    return undefined;
  }

  const message = (current as { message?: unknown }).message;
  return typeof message === 'string' ? message : undefined;
}

export function FormField<TFieldValues extends FieldValues = FieldValues>({
  name,
  label,
  type = 'text',
  placeholder,
  disabled,
  className,
}: FormFieldProps<TFieldValues>) {
  const inputId = useId();
  const { t } = useTranslation();
  const {
    register,
    formState: { errors },
  } = useFormContext<TFieldValues>();
  const errorMessage = resolveErrorMessage(errors as Record<string, unknown>, String(name));

  return (
    <div className={['form-field', className].filter(Boolean).join(' ')}>
      <label className="form-field__label" htmlFor={inputId}>
        {t(label)}
      </label>
      <input
        id={inputId}
        dir="auto"
        type={type}
        className="form-field__input"
        placeholder={placeholder ? t(placeholder) : undefined}
        aria-invalid={Boolean(errorMessage)}
        aria-describedby={errorMessage ? `${inputId}-error` : undefined}
        disabled={disabled}
        {...register(name)}
      />
      {errorMessage && (
        <span className="form-field__error" id={`${inputId}-error`} role="alert">
          {t(errorMessage, { defaultValue: errorMessage })}
        </span>
      )}
    </div>
  );
}
