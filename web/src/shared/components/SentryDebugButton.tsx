/**
 * Sentry Debug Button — triggers a test error to verify Sentry integration.
 *
 * Add this component temporarily to any page to confirm errors are captured.
 */

import * as Sentry from '@sentry/react';

export function SentryDebugButton() {
  return (
    <button
      type="button"
      onClick={() => {
        Sentry.logger.info('User triggered test error', {
          action: 'test_error_button_click',
        });
        Sentry.addBreadcrumb({
          category: 'sentry-debug',
          message: 'User triggered test error',
          level: 'info',
        });
        throw new Error('This is a Sentry test error from the React app!');
      }}
      style={{
        padding: '8px 16px',
        backgroundColor: '#dc2626',
        color: '#fff',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
      }}
    >
      Break the world (Sentry test)
    </button>
  );
}
