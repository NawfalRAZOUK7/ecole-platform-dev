import { api } from '@/services/api/client';
import type { FeedItem } from './types';

export interface FeedListParams extends Record<string, string | number | undefined> {
  cursor?: string;
}

export const feedService = {
  list(params: FeedListParams = {}) {
    return api.list<FeedItem>('/feed', params);
  },
};
