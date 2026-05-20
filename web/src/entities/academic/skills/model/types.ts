export interface SkillDimension {
  id: string;
  code: string;
  name_fr: string;
  name_ar: string;
  name_en: string;
  description_fr?: string | null;
  icon?: string | null;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateSkillDimensionPayload {
  code: string;
  name_fr: string;
  name_ar: string;
  name_en: string;
  description_fr?: string | null;
  icon?: string | null;
  display_order: number;
  is_active: boolean;
}

export interface SkillMilestone {
  id: string;
  dimension_id: string;
  dimension_code?: string | null;
  code: string;
  name_fr: string;
  name_ar: string;
  level: number;
  rule_config: Record<string, unknown>;
  badge_icon?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateSkillMilestonePayload {
  dimension_id: string;
  code: string;
  name_fr: string;
  name_ar: string;
  level: number;
  rule_config: Record<string, unknown>;
  badge_icon?: string | null;
  is_active: boolean;
}

export interface SkillProgressItem {
  id: string;
  student_id: string;
  school_id: string;
  milestone_id: string;
  milestone_code?: string | null;
  dimension_id?: string | null;
  dimension_code?: string | null;
  unlocked_at?: string | null;
  current_value: number;
  status: string;
  evidence?: Record<string, unknown> | null;
  academic_year_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface SkillPassport {
  id: string;
  student_id: string;
  school_id: string;
  academic_year_id: string;
  generated_at: string;
  pdf_url?: string | null;
  total_milestones: number;
  unlocked_milestones: number;
  overall_score: number;
  created_at: string;
  updated_at?: string | null;
  progress_items: SkillProgressItem[];
}

export interface SkillEvaluation {
  student_id: string;
  school_id: string;
  academic_year_id: string;
  evaluated_at: string;
  total_milestones: number;
  unlocked_milestones: number;
  overall_score: number;
  metrics: Record<string, number>;
  progress_items: SkillProgressItem[];
}

export interface SkillDimensionAnalytics {
  dimension_id: string;
  code: string;
  name_fr: string;
  milestone_count: number;
  unlocked_count: number;
  average_progress: number;
}

export interface SkillClassAnalytics {
  class_id: string;
  school_id: string;
  academic_year_id: string;
  student_count: number;
  passport_count: number;
  active_milestone_count: number;
  progress_record_count: number;
  unlocked_record_count: number;
  average_overall_score: number;
  dimension_summaries: SkillDimensionAnalytics[];
}

export interface SkillSchoolAnalytics {
  school_id: string;
  academic_year_id: string;
  student_count: number;
  passport_count: number;
  active_milestone_count: number;
  progress_record_count: number;
  unlocked_record_count: number;
  average_overall_score: number;
  dimension_summaries: SkillDimensionAnalytics[];
}

export interface SkillLeaderboardEntry {
  rank: number;
  student_id: string;
  alias: string;
  total_milestones: number;
  unlocked_milestones: number;
  overall_score: number;
}
