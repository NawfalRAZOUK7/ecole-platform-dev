import { lazy } from 'react';

export const ProfilePage = lazy(() =>
  import('./profile/ui/ProfilePage').then((m) => ({ default: m.ProfilePage })),
);
export const SessionsPage = lazy(() =>
  import('./profile/ui/SessionsPage').then((m) => ({ default: m.SessionsPage })),
);
export const TwoFactorPage = lazy(() =>
  import('./profile/ui/TwoFactorPage').then((m) => ({ default: m.TwoFactorPage })),
);
export const LoginHistoryPage = lazy(() =>
  import('./profile/ui/LoginHistoryPage').then((m) => ({ default: m.LoginHistoryPage })),
);

export const MyChildrenPage = lazy(() =>
  import('./family/ui/MyChildrenPage').then((m) => ({ default: m.MyChildrenPage })),
);
export const SharedReviewPage = lazy(() =>
  import('./family/ui/SharedReviewPage').then((m) => ({ default: m.SharedReviewPage })),
);
export const ReviewDetailPage = lazy(() =>
  import('./family/ui/ReviewDetailPage').then((m) => ({ default: m.ReviewDetailPage })),
);

export const ParentChildLinksPage = lazy(() =>
  import('./parent-child-links/ui/ParentChildLinksPage').then((m) => ({
    default: m.ParentChildLinksPage,
  })),
);

export const StudentHomePage = lazy(() =>
  import('./student/ui/StudentHomePage').then((m) => ({ default: m.StudentHomePage })),
);
