export function isImage(mimeType: string) {
  return mimeType.startsWith('image/');
}

export function isPdf(mimeType: string) {
  return mimeType === 'application/pdf';
}

export function humanSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function openSignedUrl(url: string | null) {
  if (!url) return;
  const href = url.startsWith('http') ? url : `${window.location.origin}${url}`;
  window.open(href, '_blank', 'noopener,noreferrer');
}
