import { lazy } from 'react';

export const DashboardPage = lazy(() =>
  import('./ui/DashboardPage').then((m) => ({ default: m.DashboardPage })),
);
export const UsersPage = lazy(() =>
  import('./ui/UsersPage').then((m) => ({ default: m.UsersPage })),
);
export const InvitationsPage = lazy(() =>
  import('./ui/InvitationsPage').then((m) => ({ default: m.InvitationsPage })),
);
export const AuditLogPage = lazy(() =>
  import('./ui/AuditLogPage').then((m) => ({ default: m.AuditLogPage })),
);
export const JustificationReviewPage = lazy(() =>
  import('./ui/JustificationReviewPage').then((m) => ({ default: m.JustificationReviewPage })),
);
export const BatchRegisterPage = lazy(() =>
  import('./ui/BatchRegisterPage').then((m) => ({ default: m.BatchRegisterPage })),
);
export const ComplianceDashboardPage = lazy(() =>
  import('./compliance/ui/ComplianceDashboardPage').then((m) => ({
    default: m.ComplianceDashboardPage,
  })),
);
export const CurriculumMappingPage = lazy(() =>
  import('./compliance/ui/CurriculumMappingPage').then((m) => ({
    default: m.CurriculumMappingPage,
  })),
);
export const ComplianceReportPage = lazy(() =>
  import('./compliance/ui/ComplianceReportPage').then((m) => ({
    default: m.ComplianceReportPage,
  })),
);
