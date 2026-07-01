/**
 * Tests for src/core/ws/WebSocketClient.ts
 * Note: wsClient is a singleton with heartbeat timers; tests use advanceTimersByTime
 * to avoid infinite loop from the heartbeat interval.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { wsClient, type WsEvent } from '@/core/ws/WebSocketClient';
import { setAccessToken } from '@/core/api/client';

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((evt: { data: string }) => void) | null = null;
  onerror: ((evt: unknown) => void) | null = null;
  onclose: ((evt: { code: number; reason: string; wasClean: boolean }) => void) | null = null;
  readyState = 1;
  sentMessages: string[] = [];

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }

  triggerOpen() {
    this.onopen?.();
  }
  triggerMessage(event: WsEvent) {
    this.onmessage?.({ data: JSON.stringify(event) });
  }
  triggerMalformed() {
    this.onmessage?.({ data: 'not-json{{{' });
  }
  triggerError() {
    this.onerror?.({ type: 'error' });
  }
  triggerClose(code = 1006) {
    this.readyState = 3;
    this.onclose?.({ code, reason: '', wasClean: code === 1000 });
  }
  send(data: string) {
    this.sentMessages.push(data);
  }
  close() {
    this.triggerClose(1000);
  }
}

function getLatestWs() {
  return MockWebSocket.instances[MockWebSocket.instances.length - 1];
}

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.useFakeTimers();
  vi.stubGlobal('WebSocket', MockWebSocket);
  setAccessToken('test-access-token');
  wsClient.disconnect();
});

afterEach(() => {
  wsClient.disconnect();
  setAccessToken(null);
  vi.clearAllTimers();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('WebSocketClient', () => {
  it('is not connected initially', () => {
    expect(wsClient.connected).toBe(false);
  });

  it('connects and becomes connected after open event', () => {
    wsClient.connect();
    expect(getLatestWs()).toBeDefined();
    getLatestWs().triggerOpen();
    expect(wsClient.connected).toBe(true);
  });

  it('does not create WebSocket when no access token', () => {
    setAccessToken(null);
    wsClient.connect();
    expect(MockWebSocket.instances).toHaveLength(0);
    expect(wsClient.connected).toBe(false);
  });

  it('subscribes to WS events', () => {
    wsClient.connect();
    const ws = getLatestWs();
    ws.triggerOpen();

    const received: WsEvent[] = [];
    const unsub = wsClient.subscribe((evt) => received.push(evt));

    ws.triggerMessage({ event: 'notification_created', data: { id: '1' } });
    expect(received).toHaveLength(1);
    expect(received[0].event).toBe('notification_created');

    unsub();
    ws.triggerMessage({ event: 'grade_published', data: {} });
    expect(received).toHaveLength(1); // no more after unsub
  });

  it('disconnects and is no longer connected', () => {
    wsClient.connect();
    getLatestWs().triggerOpen();
    expect(wsClient.connected).toBe(true);

    wsClient.disconnect();
    expect(wsClient.connected).toBe(false);
  });

  it('responds to ping with pong', () => {
    wsClient.connect();
    const ws = getLatestWs();
    ws.triggerOpen();
    ws.triggerMessage({ event: 'ping', data: {} });
    expect(ws.sentMessages.some((m) => m.includes('"pong"'))).toBe(true);
  });

  it('ignores malformed JSON gracefully', () => {
    wsClient.connect();
    const ws = getLatestWs();
    ws.triggerOpen();

    const received: WsEvent[] = [];
    wsClient.subscribe((evt) => received.push(evt));

    ws.triggerMalformed();
    expect(received).toHaveLength(0); // no crash
  });

  it('reconnects after abnormal close with delay', () => {
    wsClient.connect();
    const ws = getLatestWs();
    ws.triggerOpen();
    expect(wsClient.connected).toBe(true);

    ws.triggerClose(1006); // abnormal
    expect(wsClient.connected).toBe(false);

    // Advance past reconnect delay (1000ms initial)
    vi.advanceTimersByTime(1500);
    // A new WS instance should have been created
    expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(2);
  });

  it('does not reconnect after intentional disconnect (clean close)', () => {
    wsClient.connect();
    const initialCount = MockWebSocket.instances.length;
    getLatestWs().triggerOpen();

    wsClient.disconnect(); // sets _shouldConnect = false
    vi.advanceTimersByTime(5000);

    expect(MockWebSocket.instances.length).toBe(initialCount); // no new WS
  });

  it('handles WebSocket constructor throwing', () => {
    vi.stubGlobal(
      'WebSocket',
      class {
        constructor() {
          throw new Error('WS unavailable');
        }
      },
    );
    expect(() => wsClient.connect()).not.toThrow();
    expect(wsClient.connected).toBe(false);
  });

  it('handles WS error event without crashing', () => {
    wsClient.connect();
    const ws = getLatestWs();
    ws.triggerOpen();
    expect(() => ws.triggerError()).not.toThrow();
  });
});
