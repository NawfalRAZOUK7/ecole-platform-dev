import { lazy } from 'react';

export const BudgetListPage = lazy(() =>
  import('./budgets/ui/BudgetListPage').then((m) => ({ default: m.BudgetListPage })),
);
export const BudgetRequestPage = lazy(() =>
  import('./budgets/ui/BudgetRequestPage').then((m) => ({ default: m.BudgetRequestPage })),
);
export const BudgetAnalyticsPage = lazy(() =>
  import('./budgets/ui/BudgetAnalyticsPage').then((m) => ({ default: m.BudgetAnalyticsPage })),
);
export const BudgetDetailPage = lazy(() =>
  import('./budgets/ui/BudgetDetailPage').then((m) => ({ default: m.BudgetDetailPage })),
);

export const InvoicesPage = lazy(() =>
  import('./invoices/ui/InvoicesPage').then((m) => ({ default: m.InvoicesPage })),
);
export const InvoiceDetailPage = lazy(() =>
  import('./invoices/ui/InvoiceDetailPage').then((m) => ({ default: m.InvoiceDetailPage })),
);

export const FeeStructuresPage = lazy(() =>
  import('./ui/FeeStructuresPage').then((m) => ({ default: m.FeeStructuresPage })),
);
export const FeeAssignmentsPage = lazy(() =>
  import('./ui/FeeAssignmentsPage').then((m) => ({ default: m.FeeAssignmentsPage })),
);
export const GenerateInvoicesPage = lazy(() =>
  import('./ui/GenerateInvoicesPage').then((m) => ({ default: m.GenerateInvoicesPage })),
);
export const SiblingPolicyPage = lazy(() =>
  import('./ui/SiblingPolicyPage').then((m) => ({ default: m.SiblingPolicyPage })),
);
export const LateFeePolicyPage = lazy(() =>
  import('./ui/LateFeePolicyPage').then((m) => ({ default: m.LateFeePolicyPage })),
);
export const PaymentPlansPage = lazy(() =>
  import('./ui/PaymentPlansPage').then((m) => ({ default: m.PaymentPlansPage })),
);
export const PaymentPlanDetailPage = lazy(() =>
  import('./ui/PaymentPlanDetailPage').then((m) => ({ default: m.PaymentPlanDetailPage })),
);
