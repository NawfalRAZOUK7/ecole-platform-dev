/**
 * École Platform — Entry Point
 *
 * Wraps App in providers: BrowserRouter, AuthProvider.
 * Initialises i18n before render.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/services/auth/AuthContext';
import App from '@/app/App';

// Initialise i18n (side-effect import — must be before App render)
import '@/shared/i18n';

// Global styles
import '@/app/styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
