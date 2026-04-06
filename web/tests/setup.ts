import '@testing-library/jest-dom';
import { ReadableStream, TransformStream, WritableStream } from 'node:stream/web';
import { afterAll, afterEach, beforeAll } from 'vitest';

class ResizeObserverMock {
  observe() {}

  unobserve() {}

  disconnect() {}
}

if (!globalThis.ReadableStream) {
  globalThis.ReadableStream = ReadableStream;
}

if (!globalThis.WritableStream) {
  globalThis.WritableStream = WritableStream;
}

if (!globalThis.TransformStream) {
  globalThis.TransformStream = TransformStream;
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
