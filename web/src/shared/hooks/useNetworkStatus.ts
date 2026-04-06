import { useEffect, useRef, useState } from 'react';

interface NetworkStatus {
  isOnline: boolean;
  wasOffline: boolean;
}

export function useNetworkStatus(): NetworkStatus {
  const [isOnline, setIsOnline] = useState(() => window.navigator.onLine);
  const [wasOffline, setWasOffline] = useState(false);
  const reconnectTimer = useRef<number | null>(null);

  useEffect(() => {
    function clearReconnectTimer() {
      if (reconnectTimer.current !== null) {
        window.clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
    }

    function handleOnline() {
      setIsOnline(true);
      setWasOffline(true);
      clearReconnectTimer();
      reconnectTimer.current = window.setTimeout(() => {
        setWasOffline(false);
      }, 3000);
    }

    function handleOffline() {
      clearReconnectTimer();
      setIsOnline(false);
      setWasOffline(false);
    }

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      clearReconnectTimer();
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { isOnline, wasOffline };
}
