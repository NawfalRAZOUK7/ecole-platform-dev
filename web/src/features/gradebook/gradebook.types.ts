export interface GradebookEntry {
  student_id: string;
  student_name: string;
  grades: Record<string, number | null>;
  weighted_average: number;
}

export interface GradebookColumn {
  assessment_id: string;
  title: string;
  weight: number;
  max_score: 20;
  date: string;
  type: 'exam' | 'quiz' | 'homework' | 'project';
}

export interface GradebookGrid {
  class_id: string;
  class_name: string;
  columns: GradebookColumn[];
  entries: GradebookEntry[];
}

export interface BulkGradeUpdate {
  class_id: string;
  grades: Array<{
    student_id: string;
    assessment_id: string;
    value: number;
  }>;
}

export interface GradebookWeightedSummary {
  class_id: string;
  class_average: number;
  pass_rate: number;
  highest_average: number;
  lowest_average: number;
}

export interface StudentGradeRow {
  assessment_id: string;
  title: string;
  date: string;
  weight: number;
  type: GradebookColumn['type'];
  value: number | null;
}

export interface StudentGradeSummary {
  student_id: string;
  student_name: string;
  class_id: string;
  class_name: string;
  overall_average: number;
  grades: StudentGradeRow[];
}

export interface GradebookExportResponse {
  download_url?: string;
  file_name?: string;
}
