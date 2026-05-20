/**
 * École Platform — Entry Point
 *
 * Wraps App in providers: BrowserRouter, AuthProvider.
 * Initialises i18n before render.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import * as Sentry from '@sentry/react';
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  BrowserRouter,
  useLocation,
  useNavigationType,
  createRoutesFromChildren,
  matchRoutes,
} from 'react-router-dom';
import { AuthProvider } from '@/app/providers/AuthContext';
import App from '@/app/App';

// Initialise i18n (side-effect import — must be before App render)
import '@/shared/i18n';

// Global styles
import '@/app/styles.css';
import '@/shared/styles/animations.css';
import '@/shared/styles/glassmorphism.css';

const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN ?? '';
const SENTRY_ENV = import.meta.env.MODE ?? 'development';
const IS_PROD = SENTRY_ENV === 'production';

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENV,
    sendDefaultPii: false,
    enableLogs: true,
    integrations: [
      Sentry.browserTracingIntegration({
        instrumentNavigation: true,
        instrumentPageLoad: true,
      }),
      Sentry.replayIntegration(),
      Sentry.reactRouterV6BrowserTracingIntegration({
        useEffect: React.useEffect,
        useLocation,
        useNavigationType,
        createRoutesFromChildren,
        matchRoutes,
      }),
    ],
    tracesSampleRate: IS_PROD ? 0.1 : 1,
    tracePropagationTargets: ['localhost', /^https:\/\/.*\.ecole-platform\.ma/],
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1,
  });
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      Sentry.captureException(error);
      console.error(error);
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      Sentry.captureException(error);
      console.error(error);
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
