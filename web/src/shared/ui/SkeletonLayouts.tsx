/**
 * Reusable skeleton layouts built on the shimmer `Skeleton` primitive.
 *
 * Use these in place of a full-page spinner (`LoadingState`) on list, table and
 * dashboard loads so the page keeps its shape while data arrives — a large
 * perceived-speed improvement. All shimmer animation is automatically disabled
 * by the prefers-reduced-motion block in styles.css.
 */

import { memo } from 'react';
import { Skeleton } from '@/shared/ui/Skeleton';

interface CountProps {
  count?: number;
}

/** Vertical list of card-shaped rows (e.g. users, invitations, content cards). */
export const ListSkeleton = memo(function ListSkeleton({ count = 6 }: CountProps) {
  return (
    <div className="card-list" role="status" aria-label="Loading" aria-busy="true">
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          className="card"
          style={{ display: 'flex', gap: 12, alignItems: 'center' }}
        >
          <Skeleton variant="circle" width="40px" height="40px" />
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <Skeleton variant="line" width="45%" height="14px" />
            <Skeleton variant="line" width="70%" height="12px" />
          </div>
          <Skeleton variant="line" width="64px" height="24px" />
        </div>
      ))}
    </div>
  );
});

/** Table-shaped skeleton with a header row and body rows. */
export const TableSkeleton = memo(function TableSkeleton({
  rows = 8,
  columns = 4,
}: {
  rows?: number;
  columns?: number;
}) {
  return (
    <div className="card" role="status" aria-label="Loading" aria-busy="true">
      <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
        {Array.from({ length: columns }, (_, c) => (
          <Skeleton key={`h-${c}`} variant="line" width="100%" height="12px" />
        ))}
      </div>
      {Array.from({ length: rows }, (_, r) => (
        <div key={`r-${r}`} style={{ display: 'flex', gap: 16, padding: '10px 0' }}>
          {Array.from({ length: columns }, (_, c) => (
            <Skeleton key={`c-${r}-${c}`} variant="line" width="100%" height="14px" />
          ))}
        </div>
      ))}
    </div>
  );
});

/** Grid of stat-card skeletons for dashboard headers. */
export const StatGridSkeleton = memo(function StatGridSkeleton({ count = 4 }: CountProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      aria-busy="true"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 16,
      }}
    >
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          className="card"
          style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
        >
          <Skeleton variant="line" width="50%" height="12px" />
          <Skeleton variant="line" width="70%" height="28px" />
          <Skeleton variant="line" width="40%" height="12px" />
        </div>
      ))}
    </div>
  );
});
