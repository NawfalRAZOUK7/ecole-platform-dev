import { useEffect, useState } from 'react';
import type { ApiError } from '@/services/api/client';

export function useDismissibleError(error: ApiError | string | null) {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setDismissed(false);
  }, [error]);

  return {
    error: dismissed ? null : error,
    dismiss: () => setDismissed(true),
  };
}
