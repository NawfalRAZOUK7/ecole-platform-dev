import { lazy } from 'react';

export const SyncStatusPage = lazy(() =>
  import('./ui/SyncStatusPage').then((m) => ({ default: m.SyncStatusPage })),
);
export const SyncConflictsPage = lazy(() =>
  import('./ui/SyncConflictsPage').then((m) => ({ default: m.SyncConflictsPage })),
);
export const SyncSettingsPage = lazy(() =>
  import('./ui/SyncSettingsPage').then((m) => ({ default: m.SyncSettingsPage })),
);
