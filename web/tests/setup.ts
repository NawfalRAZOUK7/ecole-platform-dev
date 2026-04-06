import '@testing-library/jest-dom';
import { ReadableStream, TransformStream, WritableStream } from 'node:stream/web';
import { afterAll, afterEach, beforeAll } from 'vitest';

if (!globalThis.ReadableStream) {
  globalThis.ReadableStream = ReadableStream;
}

if (!globalThis.WritableStream) {
  globalThis.WritableStream = WritableStream;
}

if (!globalThis.TransformStream) {
  globalThis.TransformStream = TransformStream;
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
