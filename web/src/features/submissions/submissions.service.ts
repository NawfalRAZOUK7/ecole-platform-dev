import {
  getAccessToken,
  getSchoolId,
  api,
  getDownloadUrl,
  type DownloadMetadata,
} from '@/services/api/client';
import { directUpload, shouldUseDirect } from '@/services/uploads/directUpload';

export interface AssignmentOption {
  id: string;
  title: string;
  course_id: string;
  due_at: string | null;
  total_points: number;
  exercise_type?: string;
  exercise_pdf_path?: string | null;
}

export interface ExercisePdfUploadResponse {
  id: string;
  exercise_pdf_path: string;
  checksum: string;
  file_size: number;
}

export const submissionsService = {
  listAssignments() {
    return api.list<AssignmentOption>('/assignments');
  },

  createSubmission(assignmentId: string) {
    return api.post<{ id: string }>('/submissions', {
      assignment_id: assignmentId,
    });
  },

  async uploadSubmissionFile(
    submissionId: string,
    file: File,
    fileTypeHint?: string,
    onProgress?: (completed: number) => void,
  ) {
    if (shouldUseDirect(file, 'submission_file')) {
      const schoolId = getSchoolId();
      if (!schoolId) throw new Error('No school context available');
      await directUpload({
        kind: 'submission_file',
        scope: { school_id: schoolId, submission_id: submissionId },
        file,
        onProgress,
      });
      return;
    }

    // Small files: legacy multipart path through the backend
    return new Promise<void>((resolve, reject) => {
      const formData = new FormData();
      formData.append('file', file);
      if (fileTypeHint) {
        formData.append('file_type_hint', fileTypeHint);
      }

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `/api/v1/submissions/${submissionId}/files`);

      const token = getAccessToken();
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && onProgress) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
          return;
        }
        reject(new Error('Upload failed'));
      };

      xhr.onerror = () => reject(new Error('Upload failed'));
      xhr.send(formData);
    });
  },

  finalizeSubmission(submissionId: string) {
    return api.post<void>(`/submissions/${submissionId}/submit`);
  },

  async uploadExercisePdf(assignmentId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {};
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`/api/v1/assignments/${assignmentId}/exercise-pdf`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      headers,
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(body?.error?.message || 'Upload failed');
    }

    const body = await response.json().catch(() => null);
    return (body?.data ?? body) as ExercisePdfUploadResponse;
  },

  downloadExercisePdf(assignmentId: string) {
    return getDownloadUrl(`/assignments/${assignmentId}/exercise-pdf`);
  },

  overridePenalty(submissionId: string, payload: { penalty_override: number; reason?: string }) {
    return api.post<void>(`/submissions/${submissionId}/override-penalty`, payload);
  },

  uploadFiles(submissionId: string, files: File[]) {
    return Promise.all(
      files.map((file) => submissionsService.uploadSubmissionFile(submissionId, file)),
    );
  },

  getFile(submissionId: string, fileId: string): Promise<DownloadMetadata> {
    return getDownloadUrl(`/submissions/${submissionId}/files/${fileId}`);
  },

  previewSubmission(submissionId: string) {
    return api.get<{ preview_url: string; status: string }>(`/submissions/${submissionId}/preview`);
  },
};
