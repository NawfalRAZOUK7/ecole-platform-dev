export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  field_errors?: Record<string, string[]>;
}

export interface ApiSuccess<T> {
  data: T;
  message?: string;
}

export type ApiResponse<T> =
  | { data: T; error: null }
  | { data: null; error: ApiError };
