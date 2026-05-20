import { api } from '@/core/api/client';

export interface ChartDataset {
  label: string;
  data: number[];
}

export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface AttendanceData {
  overview: ChartData & { summary: { total: number; present: number; attendance_rate: number } };
  trend: ChartData;
}

export interface ContentCompletion {
  summary: { total: number; completed: number; completion_rate: number };
  labels: string[];
  datasets: ChartDataset[];
}

export interface ProgressData {
  student_id: string;
  student_name: string;
  grade_trends: ChartData;
  content_completion: ContentCompletion;
  activity_scores: ChartData;
  attendance: AttendanceData;
  assessment_results: ChartData;
}

export interface ChildSummary {
  student_id: string;
  student_name: string;
  grade_average: number;
  attendance_rate: number;
  content_completion_rate: number;
  latest_grade?: {
    score: number;
    assignment: string;
  };
}

export interface ChildrenResponse {
  child_count: number;
  children: ChildSummary[];
  charts: {
    comparison: {
      labels: string[];
      datasets: ChartDataset[];
    };
  };
}

export const progressService = {
  getProgress(studentId?: string | null) {
    return api.get<{ data: ProgressData }>(
      studentId ? `/progress/student/${studentId}` : '/progress/me',
    );
  },

  getChildrenOverview() {
    return api.get<{ data: ChildrenResponse }>('/progress/children');
  },

  getStudentProgress(studentId: string) {
    return api.get<{ data: ProgressData }>(`/progress/student/${studentId}`);
  },

  getMyProgress() {
    return api.get<{ data: ProgressData }>('/progress/me');
  },
};
