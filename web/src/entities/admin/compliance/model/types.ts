export interface MenCurriculum {
  id: string;
  level: string;
  grade: string;
  subject: string;
  academic_year: string;
  version: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateMenCurriculumPayload {
  level: string;
  grade: string;
  subject: string;
  academic_year: string;
  version: string;
  is_active: boolean;
}

export interface MenObjective {
  id: string;
  curriculum_id: string;
  curriculum_subject?: string | null;
  code: string;
  title_fr: string;
  title_ar: string;
  description_fr?: string | null;
  trimester: number;
  unit_number: number;
  is_mandatory: boolean;
  hours_recommended?: number | null;
  display_order: number;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateMenObjectivePayload {
  code: string;
  title_fr: string;
  title_ar: string;
  description_fr?: string | null;
  trimester: number;
  unit_number: number;
  is_mandatory: boolean;
  hours_recommended?: number | null;
  display_order: number;
}

export interface CurriculumMapping {
  id: string;
  school_id: string;
  objective_id: string;
  objective_code?: string | null;
  curriculum_id?: string | null;
  course_id?: string | null;
  content_item_id?: string | null;
  mapped_by: string;
  mapped_at: string;
  coverage_percent: number;
  notes?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateCurriculumMappingPayload {
  objective_id: string;
  course_id?: string | null;
  content_item_id?: string | null;
  coverage_percent: number;
  notes?: string | null;
}

export interface ComplianceDashboardItem {
  curriculum_id: string;
  level: string;
  grade: string;
  subject: string;
  academic_year: string;
  total_objectives: number;
  mapped_objectives: number;
  unmapped_objectives: number;
  compliance_percent: number;
}

export interface ComplianceDashboard {
  school_id: string;
  academic_year_id?: string | null;
  curriculum_count: number;
  total_objectives: number;
  mapped_objectives: number;
  overall_compliance_percent: number;
  items: ComplianceDashboardItem[];
}

export interface ComplianceReport {
  id: string;
  school_id: string;
  curriculum_id: string;
  curriculum_subject?: string | null;
  curriculum_grade?: string | null;
  curriculum_level?: string | null;
  generated_at: string;
  generated_by: string;
  total_objectives: number;
  mapped_objectives: number;
  compliance_percent: number;
  unmapped_objectives: string[];
  pdf_url?: string | null;
  academic_year_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface GenerateComplianceReportPayload {
  curriculum_id: string;
  academic_year_id: string;
}
