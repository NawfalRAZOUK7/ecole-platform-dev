import { memo, type ReactNode } from 'react';

interface BadgeProps {
  variant: 'success' | 'warning' | 'error' | 'info' | 'neutral';
  children: ReactNode;
  size?: 'sm' | 'md';
}

export const Badge = memo(function Badge({ variant, children, size = 'md' }: BadgeProps) {
  return (
    <span className={`badge badge--${variant} badge--${size}`}>
      {children}
    </span>
  );
});
