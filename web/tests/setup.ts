process.env.NODE_ENV = 'test';

import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll } from 'vitest';
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

const { server } = await import('./utils/mocks');

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
