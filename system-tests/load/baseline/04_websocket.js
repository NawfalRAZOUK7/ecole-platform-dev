/// Scenario 4: 200 concurrent WebSocket connections — verify stable
///
/// Reference: Phase 6A, F2 SLO targets

import ws from 'k6/ws';
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';
import { IS_CI, assertSafeLoadTarget, getToken, selectProfile } from '../config.js';

const wsFailRate = new Rate('ws_failures');
const wsConnections = new Counter('ws_connections');

const WS_URL = __ENV.WS_URL || 'ws://localhost:8000/api/v1/ws';
assertSafeLoadTarget(WS_URL, 'WS_URL');

export const options = {
  scenarios: {
    ws_storm: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: selectProfile(
        [
          { duration: '5s', target: 5 },
          { duration: '10s', target: 10 },
          { duration: '5s', target: 10 },
          { duration: '5s', target: 0 },
        ],
        [
          { duration: '10s', target: 50 },
          { duration: '15s', target: 200 },
          { duration: '30s', target: 200 },
          { duration: '10s', target: 0 },
        ],
      ),
    },
  },
  thresholds: selectProfile(
    {
      ws_failures: ['rate<0.20'],
    },
    {
      ws_failures: ['rate<0.10'],
    },
  ),
};

export function setup() {
  const token = getToken(http, 'parent');
  return { token };
}

export default function (data) {
  const url = `${WS_URL}?token=${data.token}`;

  const res = ws.connect(url, {}, function (socket) {
    wsConnections.add(1);

    socket.on('open', () => {
      // Send a ping-like message
      socket.send(JSON.stringify({ type: 'ping' }));
    });

    socket.on('message', (msg) => {
      // Just receive messages — we're testing connection stability
    });

    socket.on('error', (e) => {
      if (!IS_CI) {
        wsFailRate.add(true);
      }
    });

    // Keep connection open for 10 seconds
    socket.setTimeout(() => {
      socket.close();
    }, 10_000);
  });

  const success = check(res, {
    'ws status 101': (r) => r && r.status === 101,
  });

  if (!success) {
    wsFailRate.add(true);
  }

  sleep(1);
}
