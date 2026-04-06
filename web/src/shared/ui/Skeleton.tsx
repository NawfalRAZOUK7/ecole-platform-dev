import { Fragment } from 'react';

interface SkeletonProps {
  variant: 'line' | 'card' | 'table-row' | 'circle';
  width?: string;
  height?: string;
  count?: number;
}

export function Skeleton({
  variant,
  width,
  height,
  count = 1,
}: SkeletonProps) {
  const items = Array.from({ length: count }, (_, index) => index);

  return (
    <>
      {items.map((item) => (
        <Fragment key={`${variant}-${item}`}>
          <div
            className={`skeleton skeleton--${variant}`}
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
}
