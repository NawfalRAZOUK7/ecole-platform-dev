process.env.NODE_ENV = 'test';

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, vi } from 'vitest';
import { ReadableStream, TransformStream, WritableStream } from 'web-streams-polyfill';

class ResizeObserverMock {
  observe() {}

  unobserve() {}

  disconnect() {}
}

if (!globalThis.ReadableStream) {
  globalThis.ReadableStream = ReadableStream as unknown as typeof globalThis.ReadableStream;
}

if (!globalThis.WritableStream) {
  globalThis.WritableStream = WritableStream as unknown as typeof globalThis.WritableStream;
}

if (!globalThis.TransformStream) {
  globalThis.TransformStream = TransformStream as unknown as typeof globalThis.TransformStream;
}

if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = ResizeObserverMock as typeof ResizeObserver;
}

if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = ResizeObserverMock as typeof ResizeObserver;
}

// Polyfill localStorage for forks/CI pool where jsdom may not initialize it
if (
  typeof globalThis.localStorage === 'undefined' ||
  typeof globalThis.localStorage?.getItem !== 'function'
) {
  const _store: Record<string, string> = {};
  const localStorageMock: Storage = {
    getItem: (key: string) => _store[key] ?? null,
    setItem: (key: string, value: string) => {
      _store[key] = String(value);
    },
    removeItem: (key: string) => {
      delete _store[key];
    },
    clear: () => {
      Object.keys(_store).forEach((k) => delete _store[k]);
    },
    key: (index: number) => Object.keys(_store)[index] ?? null,
    get length() {
      return Object.keys(_store).length;
    },
  };
  Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock, writable: true });
  if (typeof window !== 'undefined') {
    Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });
  }
}

const { server } = await import('./utils/mocks');

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
  vi.useRealTimers();
});

afterAll(() => {
  server.close();
});
