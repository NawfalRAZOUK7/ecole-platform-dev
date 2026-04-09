import { useEffect, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';

interface ConfirmDialogProps {
  readonly open: boolean;
  readonly title: string;
  readonly message: string;
  readonly confirmLabel?: string;
  readonly cancelLabel?: string;
  readonly variant?: 'danger' | 'warning' | 'info';
  readonly onConfirm: () => void;
  readonly onCancel: () => void;
  readonly loading?: boolean;
}

function getFocusableElements(container: HTMLElement | null) {
  if (!container) {
    return [];
  }

  return Array.from(
    container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => !element.hasAttribute('disabled') && element.tabIndex !== -1);
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  variant = 'info',
  onConfirm,
  onCancel,
  loading = false,
}: ConfirmDialogProps) {
  const { t } = useTranslation();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const labels = useMemo(
    () => ({
      title: t(title),
      message: t(message),
      confirm: t(confirmLabel || 'app.confirm', { defaultValue: confirmLabel || 'Confirm' }),
      cancel: t(cancelLabel || 'app.cancel', { defaultValue: cancelLabel || 'Cancel' }),
    }),
    [cancelLabel, confirmLabel, message, t, title],
  );

  useEffect(() => {
    if (!open) {
      previousFocusRef.current?.focus();
      return undefined;
    }

    previousFocusRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const focusable = getFocusableElements(dialogRef.current);
    focusable[0]?.focus();

    function handleGlobalKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault();
        onCancel();
        return;
      }

      if (event.key !== 'Tab') {
        return;
      }

      const dialog = dialogRef.current;
      const focusableElements = getFocusableElements(dialog);
      if (!dialog || focusableElements.length === 0) {
        return;
      }

      const first = focusableElements[0];
      const last = focusableElements[focusableElements.length - 1];
      const activeElement = document.activeElement;
      const focusIsOutsideDialog =
        !(activeElement instanceof HTMLElement) || !dialog.contains(activeElement);

      if (event.shiftKey && (activeElement === first || focusIsOutsideDialog)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (activeElement === last || focusIsOutsideDialog)) {
        event.preventDefault();
        first.focus();
      }
    }

    globalThis.addEventListener('keydown', handleGlobalKeyDown);
    return () => globalThis.removeEventListener('keydown', handleGlobalKeyDown);
  }, [onCancel, open]);

  if (!open) {
    return null;
  }

  return (
    <dialog
      ref={dialogRef}
      className="confirm-dialog__overlay"
      open
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
    >
      <button
        type="button"
        className="confirm-dialog__backdrop"
        aria-label={t('app.close', { defaultValue: 'Close dialog' })}
        tabIndex={-1}
        onClick={onCancel}
      />
      <div className="confirm-dialog">
        <div className={`confirm-dialog__content confirm-dialog__content--${variant}`}>
          <h2 id="confirm-dialog-title">{labels.title}</h2>
          <p id="confirm-dialog-message">{labels.message}</p>
          <div className="confirm-dialog__actions">
            <button type="button" className="btn btn-secondary" onClick={onCancel}>
              {labels.cancel}
            </button>
            <button
              type="button"
              className={`btn ${variant === 'danger' ? 'btn-danger' : 'btn-primary'}`}
              onClick={onConfirm}
              disabled={loading}
              aria-busy={loading ? 'true' : 'false'}
            >
              {labels.confirm}
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}
