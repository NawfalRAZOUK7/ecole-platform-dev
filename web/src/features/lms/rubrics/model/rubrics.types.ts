export interface RubricLevel {
  id: string;
  label: string;
  score: number;
  description: string;
}

export interface RubricCriterion {
  id: string;
  name: string;
  weight: number;
  levels: RubricLevel[];
}

export interface Rubric {
  id: string;
  title: string;
  description: string | null;
  subject: string | null;
  criteria: RubricCriterion[];
  max_score: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type CreateRubricCriterion = {
  name: string;
  weight: number;
  levels: Omit<RubricLevel, 'id'>[];
};

export interface CreateRubricPayload {
  title: string;
  description?: string | null;
  subject?: string | null;
  criteria: CreateRubricCriterion[];
}

export interface UpdateRubricPayload extends CreateRubricPayload {
  id: string;
}

export interface RubricGradeEntry {
  student_id: string;
  criterion_id: string;
  level_id: string;
  score: number;
}

export interface RubricGradePayload {
  rubric_id: string;
  assignment_id?: string | null;
  entries: RubricGradeEntry[];
}

export interface RubricGradeResult {
  student_id: string;
  rubric_id: string;
  total_score: number;
  max_score: number;
  percentage: number;
  entries: RubricGradeEntry[];
}

export interface RubricResultsResponse {
  rubric_id: string;
  results: RubricGradeResult[];
}
