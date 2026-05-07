import { Fragment, memo } from 'react';

interface SkeletonProps {
  variant: 'line' | 'card' | 'table-row' | 'circle';
  width?: string;
  height?: string;
  count?: number;
  shimmer?: boolean;
}

export const Skeleton = memo(function Skeleton({
  variant,
  width,
  height,
  count = 1,
  shimmer = true,
}: SkeletonProps) {
  const items = Array.from({ length: count }, (_, index) => index);

  return (
    <>
      {items.map((item) => (
        <Fragment key={`${variant}-${item}`}>
          <div
            className={`skeleton skeleton--${variant} ${shimmer ? 'skeleton--shimmer' : ''}`}
            style={{
              width,
              height,
            }}
            aria-hidden="true"
          />
        </Fragment>
      ))}
    </>
  );
});
