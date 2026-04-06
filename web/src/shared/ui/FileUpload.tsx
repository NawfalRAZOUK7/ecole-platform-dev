/**
 * Drag-drop file upload component.
 *
 * Reference: Phase 4C (from 3B) — File upload UI
 * Reusable drag-drop zone with file list, progress, and remove.
 */

import { useCallback, useRef, useState, type DragEvent } from 'react';
import { useTranslation } from 'react-i18next';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string;
  maxFiles?: number;
  maxSizeMb?: number;
  disabled?: boolean;
}

export function FileUpload({
  onFilesSelected,
  accept,
  maxFiles = 5,
  maxSizeMb = 25,
  disabled = false,
}: FileUploadProps) {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const instructionsId = 'file-upload-instructions';
  const [dragOver, setDragOver] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  const validateAndAdd = useCallback((newFiles: FileList | File[]) => {
    const errs: string[] = [];
    const valid: File[] = [];
    const maxBytes = maxSizeMb * 1024 * 1024;

    for (const file of Array.from(newFiles)) {
      if (files.length + valid.length >= maxFiles) {
        errs.push(t('fileUpload.maxFiles', { max: maxFiles }));
        break;
      }
      if (file.size > maxBytes) {
        errs.push(t('fileUpload.tooLarge', { name: file.name, max: maxSizeMb }));
        continue;
      }
      valid.push(file);
    }

    setErrors(errs);
    if (valid.length > 0) {
      const updated = [...files, ...valid];
      setFiles(updated);
      onFilesSelected(updated);
    }
  }, [files, maxFiles, maxSizeMb, onFilesSelected, t]);

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    if (!disabled) setDragOver(true);
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault();
    setDragOver(false);
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    if (e.dataTransfer.files.length > 0) {
      validateAndAdd(e.dataTransfer.files);
    }
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      validateAndAdd(e.target.files);
    }
    // Reset input so the same file can be re-selected
    if (inputRef.current) inputRef.current.value = '';
  }

  function removeFile(index: number) {
    const updated = files.filter((_, i) => i !== index);
    setFiles(updated);
    onFilesSelected(updated);
  }

  return (
    <div>
      <div
        className={`file-drop-zone ${dragOver ? 'file-drop-zone--active' : ''} ${disabled ? 'file-drop-zone--disabled' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(event) => {
          if (!disabled && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label={t('fileUpload.dragDrop')}
        aria-describedby={instructionsId}
      >
        <span style={{ fontSize: 24 }}>📎</span>
        <span>{t('fileUpload.dragDrop')}</span>
        <span id={instructionsId} style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
          {t('fileUpload.maxSize', { max: maxSizeMb })}
        </span>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept}
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />
      </div>

      {errors.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {errors.map((err, i) => (
            <div key={i} style={{ fontSize: 13, color: 'var(--color-danger)' }}>{err}</div>
          ))}
        </div>
      )}

      {files.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {files.map((file, i) => (
            <div key={i} className="file-item">
              <span style={{ flex: 1, fontSize: 14 }}>
                {file.name}
                <span style={{ color: 'var(--color-text-secondary)', marginInlineStart: 8, fontSize: 12 }}>
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
              </span>
              <button
                type="button"
                className="btn btn-danger btn-sm"
                onClick={() => removeFile(i)}
                style={{ padding: '2px 8px', fontSize: 11 }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
