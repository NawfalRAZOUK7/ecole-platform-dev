/**
 * WebSocket client — auto-connect on login, reconnect with backoff.
 *
 * Reference: Phase 4C (from 3C) — WebSocket real-time notifications
 * Connects to GET /ws?token={access_token}, receives real-time events.
 * Events: notification_created, grade_published, payment_updated, feed_new.
 */

import { getAccessToken } from '@/services/api/client';

export type WsEventType =
  | 'notification_created'
  | 'grade_published'
  | 'payment_updated'
  | 'feed_new'
  | 'message_created'
  | 'announcement_published'
  | 'welcome'
  | 'ping'
  | 'pong';

export interface WsEvent {
  event: WsEventType;
  data: Record<string, unknown>;
}

type WsListener = (event: WsEvent) => void;

const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws`;
const MAX_RECONNECT_DELAY = 30000;
const INITIAL_RECONNECT_DELAY = 1000;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Set<WsListener> = new Set();
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private _connected = false;
  private _shouldConnect = false;

  get connected(): boolean {
    return this._connected;
  }

  /** Subscribe to WS events. Returns unsubscribe function. */
  subscribe(listener: WsListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /** Connect to WebSocket (called after login). */
  connect(): void {
    this._shouldConnect = true;
    this.reconnectAttempt = 0;
    this._doConnect();
  }

  /** Disconnect (called on logout). */
  disconnect(): void {
    this._shouldConnect = false;
    this._cleanup();
  }

  private _doConnect(): void {
    if (!this._shouldConnect) return;
    const token = getAccessToken();
    if (!token) return;

    try {
      this.ws = new WebSocket(`${WS_BASE}?token=${token}`);
    } catch {
      this._scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this._connected = true;
      this.reconnectAttempt = 0;
      this._startHeartbeat();
    };

    this.ws.onmessage = (evt) => {
      try {
        const parsed: WsEvent = JSON.parse(evt.data);
        if (parsed.event === 'ping') {
          this.ws?.send(JSON.stringify({ event: 'pong' }));
          return;
        }
        this.listeners.forEach((fn) => fn(parsed));
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this._connected = false;
      this._stopHeartbeat();
      this._scheduleReconnect();
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  private _scheduleReconnect(): void {
    if (!this._shouldConnect) return;
    const delay = Math.min(
      INITIAL_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempt),
      MAX_RECONNECT_DELAY
    );
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => this._doConnect(), delay);
  }

  private _startHeartbeat(): void {
    this._stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ event: 'pong' }));
      }
    }, 25000);
  }

  private _stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private _cleanup(): void {
    this._stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close();
      }
      this.ws = null;
    }
    this._connected = false;
  }
}

/** Singleton WebSocket client instance */
export const wsClient = new WebSocketClient();
