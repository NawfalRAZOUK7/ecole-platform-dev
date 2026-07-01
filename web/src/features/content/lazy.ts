import { lazy } from 'react';

export const FeedPage = lazy(() =>
  import('./feed/ui/FeedPage').then((m) => ({ default: m.FeedPage })),
);

export const ContentPage = lazy(() =>
  import('./catalog/ui/ContentPage').then((m) => ({ default: m.ContentPage })),
);
export const ContentDetailPage = lazy(() =>
  import('./catalog/ui/ContentDetailPage').then((m) => ({ default: m.ContentDetailPage })),
);
export const ContentPlayerPage = lazy(() =>
  import('./catalog/ui/ContentPlayerPage').then((m) => ({ default: m.ContentPlayerPage })),
);

export const StudentContentPage = lazy(() =>
  import('./student/ui/StudentContentPage').then((m) => ({ default: m.StudentContentPage })),
);
export const StoryViewerPage = lazy(() =>
  import('./student/ui/StoryViewerPage').then((m) => ({ default: m.StoryViewerPage })),
);
export const ColoringViewerPage = lazy(() =>
  import('./student/ui/ColoringViewerPage').then((m) => ({ default: m.ColoringViewerPage })),
);

export const DocumentsPage = lazy(() =>
  import('./documents/ui/DocumentsPage').then((m) => ({ default: m.DocumentsPage })),
);
export const ResourcesPage = lazy(() =>
  import('./documents/ui/ResourcesPage').then((m) => ({ default: m.ResourcesPage })),
);
export const DocumentVersionsPage = lazy(() =>
  import('./documents/ui/DocumentVersionsPage').then((m) => ({ default: m.DocumentVersionsPage })),
);
export const DocumentPreviewPage = lazy(() =>
  import('./documents/ui/DocumentPreviewPage').then((m) => ({ default: m.DocumentPreviewPage })),
);
export const StudentDocumentsPage = lazy(() =>
  import('./documents/ui/StudentDocumentsPage').then((m) => ({ default: m.StudentDocumentsPage })),
);

export const ContentLibraryPage = lazy(() =>
  import('./teacher-library/ui/ContentLibraryPage').then((m) => ({
    default: m.ContentLibraryPage,
  })),
);

export const CmsContentListPage = lazy(() =>
  import('./cms/ui/ContentListPage').then((m) => ({ default: m.CmsContentListPage })),
);
export const CmsContentUploadPage = lazy(() =>
  import('./cms/ui/ContentUploadPage').then((m) => ({ default: m.CmsContentUploadPage })),
);
export const CmsContentEditPage = lazy(() =>
  import('./cms/ui/ContentEditPage').then((m) => ({ default: m.CmsContentEditPage })),
);
export const CmsReviewQueuePage = lazy(() =>
  import('./cms/ui/ReviewQueuePage').then((m) => ({ default: m.CmsReviewQueuePage })),
);
export const CmsQuizBuilderPage = lazy(() =>
  import('./cms/ui/QuizBuilderPage').then((m) => ({ default: m.CmsQuizBuilderPage })),
);
export const CmsAnalyticsPage = lazy(() =>
  import('./cms/ui/AnalyticsPage').then((m) => ({ default: m.CmsAnalyticsPage })),
);
