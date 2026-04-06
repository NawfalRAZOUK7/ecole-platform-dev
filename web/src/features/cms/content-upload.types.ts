export const CONTENT_TYPES = ['video', 'pdf', 'audio', 'interactive'];

export const LEVELS = ['maternelle', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];

export const SUBJECTS = ['math', 'french', 'arabic', 'science', 'history', 'geography', 'english', 'islamic_studies', 'art', 'sport'];

export const ACCEPT_MAP: Record<string, string> = {
  video: '.mp4,.webm',
  pdf: '.pdf',
  audio: '.mp3,.wav,.ogg',
  interactive: '*',
};

export interface BulkUploadResult {
  name: string;
  ok: boolean;
  error?: string;
}
