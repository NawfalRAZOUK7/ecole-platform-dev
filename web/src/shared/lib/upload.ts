import { api } from '@/core/api/client';

export type UploadState = 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';

export type UploadKind =
  | 'content_asset'
  | 'submission_file'
  | 'cms_asset'
  | 'document'
  | 'exercise_pdf';

export interface DirectUploadScope {
  school_id: string;
  content_item_id?: string;
  submission_id?: string;
  document_id?: string;
}

export interface DirectUploadOptions {
  kind: UploadKind;
  scope: DirectUploadScope;
  file: File;
  onProgress?: (progress: number) => void;
  onStateChange?: (state: UploadState) => void;
}

export interface DirectUploadResult {
  id: string;
  url: string;
  etag: string;
  size: number;
  mime_type: string;
}

export async function directUpload(options: DirectUploadOptions): Promise<DirectUploadResult> {
  const { kind, scope, file, onProgress, onStateChange } = options;

  onStateChange?.('pending');

  // Step 1: Request upload URL from backend
  const { data: uploadMeta } = await api.post<{
    upload_url: string;
    id: string;
    mime_type: string;
  }>('/content/upload-url', {
    kind,
    scope,
    filename: file.name,
    size: file.size,
    mime_type: file.type,
  });

  onStateChange?.('uploading');

  // Step 2: Upload to presigned URL
  const xhr = new XMLHttpRequest();
  const uploadPromise = new Promise<void>((resolve, reject) => {
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    });
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed: ${xhr.statusText}`));
      }
    });
    xhr.addEventListener('error', () => reject(new Error('Upload failed')));
    xhr.addEventListener('abort', () => reject(new Error('Upload aborted')));
  });

  xhr.open('PUT', uploadMeta.upload_url, true);
  xhr.setRequestHeader('Content-Type', file.type);
  xhr.send(file);

  await uploadPromise;

  onStateChange?.('processing');

  // Step 3: Confirm upload
  const { data: result } = await api.post<DirectUploadResult>('/content/upload-confirm', {
    upload_id: uploadMeta.id,
  });

  onStateChange?.('completed');
  return result;
}

export function shouldUseDirect(file: File, kind: UploadKind): boolean {
  // Direct upload for files > 5MB or certain kinds
  const DIRECT_UPLOAD_THRESHOLD = 5 * 1024 * 1024;
  const alwaysDirectKinds: UploadKind[] = ['content_asset', 'cms_asset', 'exercise_pdf'];
  return file.size > DIRECT_UPLOAD_THRESHOLD || alwaysDirectKinds.includes(kind);
}
