import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export function useFocusManagement() {
  const location = useLocation();

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      const heading = document.querySelector<HTMLElement>('main h1');
      const main = document.getElementById('main-content');
      const target = heading || main;

      if (!target) {
        return;
      }

      const previousTabIndex = target.getAttribute('tabindex');
      if (!target.hasAttribute('tabindex')) {
        target.setAttribute('tabindex', '-1');
      }

      target.focus();

      if (previousTabIndex === null) {
        target.addEventListener('blur', () => {
          target.removeAttribute('tabindex');
        }, { once: true });
      }
    });

    return () => window.cancelAnimationFrame(frame);
  }, [location.pathname]);
}
