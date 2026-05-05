import { useCallback, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiClientError, getDownloadUrl, type DownloadMetadata } from '@/services/api/client';

export const SIGNED_URL_DEFAULT_TTL_MS = 10 * 60 * 1000;
export const SIGNED_URL_CACHE_RATIO = 0.8;
export const SIGNED_URL_DEFAULT_STALE_MS = SIGNED_URL_DEFAULT_TTL_MS * SIGNED_URL_CACHE_RATIO;

export const signedUrlQueryKeys = {
  all: ['signed-url'] as const,
  metadata: (path: string | null) => [...signedUrlQueryKeys.all, path] as const,
};

export function getSignedUrlStaleTime(
  metadata: DownloadMetadata | undefined,
  fetchedAt = Date.now(),
) {
  if (!metadata?.expires_at) {
    return SIGNED_URL_DEFAULT_STALE_MS;
  }

  const expiresAt = Date.parse(metadata.expires_at);
  if (Number.isNaN(expiresAt)) {
    return SIGNED_URL_DEFAULT_STALE_MS;
  }

  const ttl = expiresAt - fetchedAt;
  if (ttl <= 0) {
    return 0;
  }

  return Math.floor(ttl * SIGNED_URL_CACHE_RATIO);
}

export function useSignedUrl(path: string | null | undefined) {
  const queryClient = useQueryClient();
  const enabled = Boolean(path);
  const queryKey = useMemo(() => signedUrlQueryKeys.metadata(path ?? null), [path]);

  const query = useQuery({
    queryKey,
    queryFn: () => getDownloadUrl(path!),
    enabled,
    staleTime: (queryInstance) =>
      getSignedUrlStaleTime(
        queryInstance.state.data as DownloadMetadata | undefined,
        queryInstance.state.dataUpdatedAt,
      ),
    refetchInterval: (queryInstance) => {
      const data = queryInstance.state.data as DownloadMetadata | undefined;
      if (!data) {
        return false;
      }
      const interval = getSignedUrlStaleTime(data, queryInstance.state.dataUpdatedAt);
      return interval > 0 ? interval : 1_000;
    },
    refetchOnReconnect: true,
    refetchOnWindowFocus: true,
    retry: (failureCount, error) => {
      if (error instanceof ApiClientError && error.status === 403) {
        return false;
      }
      return failureCount < 2;
    },
  });

  const refresh = useCallback(async () => {
    if (!path) {
      return undefined;
    }

    await queryClient.invalidateQueries({ queryKey, refetchType: 'none' });
    const result = await query.refetch();
    return result.data;
  }, [path, query, queryClient, queryKey]);

  const expiresAt = query.data?.expires_at ?? null;
  const isExpired = expiresAt ? Date.parse(expiresAt) <= Date.now() : false;

  return {
    ...query,
    metadata: query.data ?? null,
    url: query.data?.download_url ?? null,
    expiresAt,
    mimeType: query.data?.mime_type ?? null,
    size: query.data?.size ?? null,
    filename: query.data?.filename ?? null,
    etag: query.data?.etag ?? null,
    isExpired,
    refresh,
  };
}
