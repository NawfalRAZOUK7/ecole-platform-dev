import { getAccessToken, api } from '@/core/api/client';

export type DocumentsTab = 'mine' | 'student' | 'resources';

export interface StudentOption {
  id: string;
  full_name: string;
  email?: string;
}

export interface DocumentItem {
  id: string;
  original_filename: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  category: string;
  linked_student_id: string | null;
  linked_student_name: string | null;
  uploader_id: string;
  uploader_name: string | null;
  expires_at: string | null;
  is_expired: boolean;
  is_expiring_soon: boolean;
  download_count: number;
  thumbnail_url: string | null;
  preview_url: string | null;
  download_url: string | null;
  created_at: string;
  deduplicated: boolean;
  can_delete: boolean;
  can_hard_delete: boolean;
}

export interface ChecklistItem {
  category: string;
  required: boolean;
  description: string | null;
  status: 'uploaded' | 'missing' | 'expired';
  expires_at: string | null;
  document: DocumentItem | null;
}

export interface ResourceItem {
  id: string;
  title: string;
  description: string | null;
  subject: string | null;
  level: string | null;
  type: string;
  tags: string[];
  visibility: string;
  class_id: string | null;
  author?: string | null;
  download_count: number;
  avg_rating: number;
  rating_count: number;
  download_url: string | null;
  preview_url: string | null;
  thumbnail_url: string | null;
  document:
    | DocumentItem
    | {
        mime_type: string;
        size_bytes: number;
        preview_url: string | null;
      }
    | null;
  my_rating: number | null;
  created_at: string;
  can_edit: boolean;
  can_delete: boolean;
  can_rate: boolean;
}

export interface DocumentsOptionsPayload {
  students: StudentOption[];
  categories: string[];
}

export interface DocumentVersion {
  version_number: number;
  created_at: string;
  author_name: string | null;
  size_bytes: number;
  download_url: string | null;
  preview_url: string | null;
}

export interface DocumentPreviewInfo {
  preview_url: string | null;
  download_url: string | null;
  mime_type: string;
  original_filename: string;
}

export interface ResourceRating {
  resource_id: string;
  avg_rating: number;
  rating_count: number;
  my_rating: number | null;
}

export interface BulkDownloadStatus {
  download_url: string | null;
  status: 'pending' | 'ready' | 'expired';
}

export interface ResourceFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  q?: string;
  type?: string;
  subject?: string;
  level?: string;
  rating?: string;
  tags?: string;
}

export interface UploadDocumentPayload {
  file: File;
  category: string;
  linkedStudentId?: string;
  expiresAt?: string;
  language: string;
}

export interface DocumentLinkPayload {
  documentId: string;
  category: string;
  expiresAt?: string;
}

export interface CreateResourcePayload {
  file: File;
  title: string;
  description: string;
  subject: string;
  level: string;
  type: string;
  tags: string;
  visibility?: string;
  classId?: string;
  language: string;
}

export interface UpdateResourcePayload {
  title?: string;
  description?: string | null;
  subject?: string | null;
  level?: string | null;
  type?: string;
  visibility?: string;
  classId?: string | null;
  tags?: string[];
}

export interface DeleteDocumentResponse {
  id: string;
  deleted: boolean;
  hard_deleted: boolean;
}

export interface DeleteResourceResponse {
  id: string;
  deleted: boolean;
}

function uploadMultipart<T>(
  path: string,
  file: File,
  fields: Record<string, string>,
  language: string,
  onProgress?: (progress: number) => void,
  onRequestCreated?: (xhr: XMLHttpRequest) => void,
) {
  return new Promise<T>((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(fields).forEach(([key, value]) => {
      if (value) {
        formData.append(key, value);
      }
    });

    const xhr = new XMLHttpRequest();
    onRequestCreated?.(xhr);
    xhr.open('POST', `/api/v1${path}`);
    xhr.setRequestHeader('Accept-Language', language || 'fr');
    xhr.setRequestHeader('X-Correlation-Id', crypto.randomUUID());
    xhr.setRequestHeader('X-Client-Version', '0.1.0');
    xhr.setRequestHeader('X-Client-Platform', 'web');
    const token = getAccessToken();
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onerror = () => reject(new Error('Upload failed'));
    xhr.onabort = () => reject(new Error('Upload canceled'));
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const payload = JSON.parse(xhr.responseText);
          resolve((payload?.data ?? undefined) as T);
        } catch {
          resolve(undefined as T);
        }
        return;
      }
      try {
        const payload = JSON.parse(xhr.responseText);
        reject(new Error(payload?.error?.message || 'Upload failed'));
      } catch {
        reject(new Error('Upload failed'));
      }
    };
    xhr.send(formData);
  });
}

export const documentsService = {
  getOptions() {
    return api.get<DocumentsOptionsPayload>('/documents/options');
  },

  listMyDocuments() {
    return api.list<DocumentItem>('/documents', {
      owner: 'me',
      limit: 100,
    });
  },

  listStudentDocuments(studentId: string) {
    return api.list<DocumentItem>(`/students/${studentId}/documents`);
  },

  getStudentChecklist(studentId: string) {
    return api.get<ChecklistItem[]>(`/students/${studentId}/documents/checklist`);
  },

  listResources(params: ResourceFilters) {
    return api.list<ResourceItem>('/resources', params);
  },

  getDocument(documentId: string) {
    return api.get<DocumentItem>(`/documents/${documentId}`);
  },

  getResource(resourceId: string) {
    return api.get<ResourceItem>(`/resources/${resourceId}`);
  },

  uploadDocument(
    payload: UploadDocumentPayload,
    onProgress?: (progress: number) => void,
    onRequestCreated?: (xhr: XMLHttpRequest) => void,
  ) {
    return uploadMultipart<DocumentItem>(
      '/documents/upload',
      payload.file,
      {
        category: payload.category,
        linked_student_id: payload.linkedStudentId || '',
        expires_at: payload.expiresAt || '',
      },
      payload.language,
      onProgress,
      onRequestCreated,
    );
  },

  createResource(
    payload: CreateResourcePayload,
    onProgress?: (progress: number) => void,
    onRequestCreated?: (xhr: XMLHttpRequest) => void,
  ) {
    return uploadMultipart<ResourceItem>(
      '/resources',
      payload.file,
      {
        title: payload.title,
        description: payload.description,
        subject: payload.subject,
        level: payload.level,
        type: payload.type,
        visibility: payload.visibility || 'school',
        class_id: payload.classId || '',
        tags: payload.tags,
      },
      payload.language,
      onProgress,
      onRequestCreated,
    );
  },

  uploadResource(
    payload: CreateResourcePayload,
    onProgress?: (progress: number) => void,
    onRequestCreated?: (xhr: XMLHttpRequest) => void,
  ) {
    return documentsService.createResource(payload, onProgress, onRequestCreated);
  },

  bulkDelete(documentIds: string[]) {
    return api.post<void>('/documents/bulk-delete', { document_ids: documentIds });
  },

  deleteDocument(documentId: string, hard = false) {
    return api.delete<DeleteDocumentResponse>(
      `/documents/${documentId}${hard ? '?hard=true' : ''}`,
    );
  },

  bulkDownload(documentIds: string[]) {
    return api.post<{ download_url: string }>('/documents/bulk-download', {
      document_ids: documentIds,
    });
  },

  rateResource(resourceId: string, rating: number) {
    return api.post<void>(`/resources/${resourceId}/rate`, { rating });
  },

  getVersions(docId: string) {
    return api.get<DocumentVersion[]>(`/documents/${docId}/versions`);
  },

  getVersion(docId: string, versionNum: number) {
    return api.get<DocumentVersion>(`/documents/${docId}/versions/${versionNum}`);
  },

  restoreVersion(docId: string, versionNum: number) {
    return api.post<DocumentItem>(`/documents/${docId}/versions/${versionNum}/restore`);
  },

  downloadDocument(docId: string) {
    return api.get<{ download_url: string }>(`/documents/${docId}/download`);
  },

  previewDocument(docId: string) {
    return api.get<DocumentPreviewInfo>(`/documents/${docId}/preview`);
  },

  getBulkDownloadStatus() {
    return api.get<BulkDownloadStatus>('/documents/bulk-download');
  },

  linkStudentDocument(studentId: string, payload: DocumentLinkPayload) {
    return api.post<DocumentItem>(`/students/${studentId}/documents`, {
      document_id: payload.documentId,
      category: payload.category,
      expires_at: payload.expiresAt ?? null,
    });
  },

  async uploadStudentDocument(
    studentId: string,
    payload: UploadDocumentPayload,
    onProgress?: (progress: number) => void,
    onRequestCreated?: (xhr: XMLHttpRequest) => void,
  ) {
    const document = await documentsService.uploadDocument(
      {
        file: payload.file,
        category: payload.category,
        expiresAt: payload.expiresAt,
        language: payload.language,
      },
      onProgress,
      onRequestCreated,
    );

    return documentsService.linkStudentDocument(studentId, {
      documentId: document.id,
      category: payload.category,
      expiresAt: payload.expiresAt,
    });
  },

  getResourceRating(resourceId: string) {
    return api.get<ResourceRating>(`/resources/${resourceId}/rating`);
  },

  updateResource(resourceId: string, payload: UpdateResourcePayload) {
    const { classId, ...rest } = payload;
    return api.put<ResourceItem>(`/resources/${resourceId}`, {
      ...rest,
      ...(classId !== undefined ? { class_id: classId } : {}),
    });
  },

  deleteResource(resourceId: string) {
    return api.delete<DeleteResourceResponse>(`/resources/${resourceId}`);
  },

  downloadResource(resourceId: string) {
    return api.get<{ download_url: string }>(`/resources/${resourceId}/download`);
  },
};
