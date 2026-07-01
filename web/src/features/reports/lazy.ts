import { lazy } from 'react';

export const ReportsPage = lazy(() =>
  import('./ui/ReportsPage').then((m) => ({ default: m.ReportsPage })),
);
export const AnalyticsDashboardPage = lazy(() =>
  import('./analytics/ui/AnalyticsDashboardPage').then((m) => ({
    default: m.AnalyticsDashboardPage,
  })),
);
export const FinancialDashboardPage = lazy(() =>
  import('./financial-health/ui/FinancialDashboardPage').then((m) => ({
    default: m.FinancialDashboardPage,
  })),
);
export const FinancialSnapshotsPage = lazy(() =>
  import('./financial-health/ui/FinancialSnapshotsPage').then((m) => ({
    default: m.FinancialSnapshotsPage,
  })),
);
export const FinancialExportPage = lazy(() =>
  import('./financial-health/ui/FinancialExportPage').then((m) => ({
    default: m.FinancialExportPage,
  })),
);
