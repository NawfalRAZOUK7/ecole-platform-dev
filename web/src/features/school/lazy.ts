import { lazy } from 'react';

export const SchoolSettingsPage = lazy(() =>
  import('./settings/ui/SchoolSettingsPage').then((m) => ({ default: m.SchoolSettingsPage })),
);

export const MicroSchoolListPage = lazy(() =>
  import('./micro-schools/ui/MicroSchoolListPage').then((m) => ({
    default: m.MicroSchoolListPage,
  })),
);
export const MicroSchoolDetailPage = lazy(() =>
  import('./micro-schools/ui/MicroSchoolDetailPage').then((m) => ({
    default: m.MicroSchoolDetailPage,
  })),
);
export const MicroSchoolEnrollPage = lazy(() =>
  import('./micro-schools/ui/MicroSchoolEnrollPage').then((m) => ({
    default: m.MicroSchoolEnrollPage,
  })),
);
