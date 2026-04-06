import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNetworkStatus } from '@/shared/hooks/useNetworkStatus';

export function OfflineIndicator() {
  const { t } = useTranslation();
  const { isOnline, wasOffline } = useNetworkStatus();
  const [visible, setVisible] = useState(!isOnline);

  useEffect(() => {
    if (!isOnline) {
      setVisible(true);
      return undefined;
    }

    if (!wasOffline) {
      setVisible(false);
      return undefined;
    }

    setVisible(true);
    const timer = window.setTimeout(() => {
      setVisible(false);
    }, 2000);

    return () => window.clearTimeout(timer);
  }, [isOnline, wasOffline]);

  if (!visible) {
    return null;
  }

  return (
    <div className="offline-indicator" role="status" aria-live="polite">
      {isOnline
        ? t('network.backOnline', { defaultValue: 'Back online.' })
        : t('network.offline', { defaultValue: 'You are offline. Some features may not work.' })}
    </div>
  );
}
