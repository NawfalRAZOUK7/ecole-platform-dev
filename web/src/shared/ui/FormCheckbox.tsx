import { useId } from 'react';
import { type FieldValues, type Path, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

interface FormCheckboxProps<TFieldValues extends FieldValues = FieldValues> {
  name: Path<TFieldValues>;
  label: string;
  description?: string;
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

export function FormCheckbox<TFieldValues extends FieldValues = FieldValues>({
  name,
  label,
  description,
  disabled,
  className,
}: FormCheckboxProps<TFieldValues>) {
  const checkboxId = useId();
  const { t } = useTranslation();
  const {
    register,
    formState: { errors },
  } = useFormContext<TFieldValues>();
  const errorMessage = getError(errors as Record<string, unknown>, String(name));

  return (
    <div className={['form-checkbox', className].filter(Boolean).join(' ')}>
      <label className="form-checkbox__label" htmlFor={checkboxId}>
        <input
          id={checkboxId}
          type="checkbox"
          className="form-checkbox__input"
          disabled={disabled}
          aria-invalid={Boolean(errorMessage)}
          aria-describedby={errorMessage ? `${checkboxId}-error` : description ? `${checkboxId}-description` : undefined}
          {...register(name)}
        />
        <span className="form-checkbox__copy">
          <span>{t(label)}</span>
          {description && (
            <small className="form-checkbox__description" id={`${checkboxId}-description`}>
              {t(description)}
            </small>
          )}
        </span>
      </label>
      {errorMessage && (
        <span className="form-checkbox__error" id={`${checkboxId}-error`} role="alert">
          {t(errorMessage, { defaultValue: errorMessage })}
        </span>
      )}
    </div>
  );
}
