import { api } from '@/services/api/client';
import type { FeedItem } from './types';

const FEED_READ_STORAGE_KEY = 'ecole.feed.read-items';
const FEED_READ_EVENT = 'ecole:feed-read-state-changed';

export interface FeedListParams extends Record<string, string | number | undefined> {
  cursor?: string;
  type?: string;
}

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function readStoredIds() {
  if (!canUseStorage()) {
    return [] as string[];
  }

  try {
    const rawValue = window.localStorage.getItem(FEED_READ_STORAGE_KEY);
    if (!rawValue) {
      return [];
    }

    const parsed = JSON.parse(rawValue);
    return Array.isArray(parsed) ? parsed.filter((value): value is string => typeof value === 'string') : [];
  } catch {
    return [];
  }
}

function writeStoredIds(ids: string[]) {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.setItem(FEED_READ_STORAGE_KEY, JSON.stringify(ids));
  window.dispatchEvent(new CustomEvent(FEED_READ_EVENT));
}

export const feedService = {
  list(params: FeedListParams = {}) {
    return api.list<FeedItem>('/feed', params);
  },

  markAsRead(feedItemId: string) {
    const currentIds = new Set(readStoredIds());
    currentIds.add(feedItemId);
    writeStoredIds(Array.from(currentIds));
    return Promise.resolve({ id: feedItemId, is_read: true });
  },

  isRead(feedItemId: string) {
    return new Set(readStoredIds()).has(feedItemId);
  },

  countUnread(items: FeedItem[]) {
    const readIds = new Set(readStoredIds());
    return items.filter((item) => !readIds.has(item.id)).length;
  },

  subscribeToReadChanges(listener: () => void) {
    if (typeof window === 'undefined') {
      return () => undefined;
    }

    const wrappedListener = () => listener();
    window.addEventListener(FEED_READ_EVENT, wrappedListener);
    window.addEventListener('storage', wrappedListener);

    return () => {
      window.removeEventListener(FEED_READ_EVENT, wrappedListener);
      window.removeEventListener('storage', wrappedListener);
    };
  },
};
