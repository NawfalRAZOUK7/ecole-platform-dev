import { useCallback, useState } from 'react';

import {
  directUpload,
  type DirectUploadOptions,
  type DirectUploadResult,
  type UploadState,
} from '@/shared/lib/upload';

export interface UseDirectUploadReturn {
  state: UploadState | null;
  progress: number;
  error: string | null;
  uploadDirect: (options: DirectUploadOptions) => Promise<DirectUploadResult>;
  reset: () => void;
}

export function useDirectUpload(): UseDirectUploadReturn {
  const [state, setState] = useState<UploadState | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const uploadDirect = useCallback(async (options: DirectUploadOptions) => {
    setError(null);
    setProgress(0);
    setState(null);

    try {
      return await directUpload({
        ...options,
        onProgress: setProgress,
        onStateChange: setState,
      });
    } catch (err) {
      setState('failed');
      setError(err instanceof Error ? err.message : 'Upload failed');
      throw err;
    }
  }, []);

  const reset = useCallback(() => {
    setState(null);
    setProgress(0);
    setError(null);
  }, []);

  return { state, progress, error, uploadDirect, reset };
}
