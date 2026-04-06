import {
  useEffect,
  useMemo,
  useRef,
  type KeyboardEvent,
} from 'react';
import { useTranslation } from 'react-i18next';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

function getFocusableElements(container: HTMLElement | null) {
  if (!container) {
    return [];
  }

  return Array.from(
    container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
  ).filter((element) => !element.hasAttribute('disabled'));
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
  const dialogRef = useRef<HTMLDivElement>(null);
  const labels = useMemo(() => ({
    title: t(title),
    message: t(message),
    confirm: t(confirmLabel || 'app.confirm', { defaultValue: confirmLabel || 'Confirm' }),
    cancel: t(cancelLabel || 'app.cancel', { defaultValue: cancelLabel || 'Cancel' }),
  }), [cancelLabel, confirmLabel, message, t, title]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const focusable = getFocusableElements(dialogRef.current);
    focusable[0]?.focus();

    function handleEscape(event: globalThis.KeyboardEvent) {
      if (event.key === 'Escape') {
        onCancel();
      }
    }

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onCancel, open]);

  if (!open) {
    return null;
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== 'Tab') {
      return;
    }

    const focusable = getFocusableElements(dialogRef.current);
    if (focusable.length === 0) {
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <div
      className="confirm-dialog__overlay"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onCancel();
        }
      }}
    >
      <div
        ref={dialogRef}
        className="confirm-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-message"
        onKeyDown={handleKeyDown}
      >
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
              aria-busy={loading}
            >
              {labels.confirm}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
