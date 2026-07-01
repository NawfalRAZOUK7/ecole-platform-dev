export interface RetentionMetric {
  id: string;
  school_id: string;
  academic_year_from: string;
  academic_year_to: string;
  total_students_start: number;
  total_students_end: number;
  retained: number;
  new_enrollments: number;
  withdrawals: number;
  retention_rate: number;
  computed_at: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ComputeRetentionPayload {
  academic_year_from: string;
  academic_year_to: string;
}

export interface CashflowForecast {
  id: string;
  school_id: string;
  forecast_month: string;
  expected_income: number;
  expected_expenses: number;
  actual_income?: number | null;
  actual_expenses?: number | null;
  currency: string;
  confidence_score: number;
  computed_at: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ComputeCashflowPayload {
  months_ahead: number;
}

export interface CostPerStudentAnalysis {
  id: string;
  school_id: string;
  academic_year_id: string;
  total_operational_cost: number;
  total_students: number;
  cost_per_student: number;
  revenue_per_student: number;
  margin_per_student: number;
  currency: string;
  computed_at: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ComputeCostPerStudentPayload {
  academic_year_id: string;
}

export interface FinancialSnapshot {
  id: string;
  school_id: string;
  snapshot_date: string;
  total_receivable: number;
  total_collected: number;
  collection_rate: number;
  overdue_amount: number;
  overdue_count: number;
  avg_payment_delay_days?: number | null;
  currency: string;
  computed_at: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ComputeFinancialSnapshotPayload {
  snapshot_date?: string | null;
}

export interface FinancialHealthDashboard {
  school_id: string;
  retention: RetentionMetric | null;
  snapshot: FinancialSnapshot | null;
  cashflow: CashflowForecast | null;
}

export interface FinancialHealthTrends {
  school_id: string;
  retention_metrics: RetentionMetric[];
  snapshots: FinancialSnapshot[];
  cashflow: CashflowForecast[];
}

export interface FinancialExportResult {
  blob: Blob;
  filename: string;
}
