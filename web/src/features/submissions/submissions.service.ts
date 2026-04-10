import { getAccessToken, api } from '@/services/api/client';

export interface AssignmentOption {
  id: string;
  title: string;
  course_id: string;
  due_at: string | null;
  total_points: number;
  exercise_type?: string;
  exercise_pdf_path?: string | null;
}

async function fetchExercisePdfResponse(
  assignmentId: string,
  method: 'GET' | 'POST',
  headers: Record<string, string>,
) {
  return fetch(`/api/v1/assignments/${assignmentId}/exercise-pdf`, {
    method,
    credentials: 'include',
    headers,
  });
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

  uploadSubmissionFile(
    submissionId: string,
    file: File,
    fileTypeHint?: string,
    onProgress?: (completed: number) => void,
  ) {
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

  async generateExercisePdf(assignmentId: string) {
    const headers: Record<string, string> = {};
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetchExercisePdfResponse(assignmentId, 'POST', headers);
    if (response.ok) {
      return response.blob();
    }

    if (![405, 415, 422].includes(response.status)) {
      throw new Error('Download failed');
    }

    const fallbackResponse = await fetchExercisePdfResponse(assignmentId, 'GET', headers);
    if (!fallbackResponse.ok) {
      throw new Error('Download failed');
    }

    return fallbackResponse.blob();
  },

  downloadExercisePdf(assignmentId: string) {
    return submissionsService.generateExercisePdf(assignmentId);
  },

  overridePenalty(submissionId: string, payload: { penalty_override: number; reason?: string }) {
    return api.post<void>(`/submissions/${submissionId}/override-penalty`, payload);
  },

  uploadFiles(submissionId: string, files: File[]) {
    return Promise.all(
      files.map((file) => submissionsService.uploadSubmissionFile(submissionId, file)),
    );
  },

  getFile(submissionId: string, fileId: string) {
    return api.get<{ id: string; filename: string; download_url: string; mime_type: string }>(
      `/submissions/${submissionId}/files/${fileId}`,
    );
  },

  previewSubmission(submissionId: string) {
    return api.get<{ preview_url: string; status: string }>(`/submissions/${submissionId}/preview`);
  },
};
