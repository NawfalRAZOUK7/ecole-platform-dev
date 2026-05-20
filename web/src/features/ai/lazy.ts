import { lazy } from 'react';

export const BadgesPage = lazy(() =>
  import('./badges/ui/BadgesPage').then((m) => ({ default: m.BadgesPage })),
);

export const RewardsPage = lazy(() =>
  import('./rewards/ui/RewardsPage').then((m) => ({ default: m.RewardsPage })),
);
export const StudentRewardsPage = lazy(() =>
  import('./rewards/ui/StudentRewardsPage').then((m) => ({ default: m.StudentRewardsPage })),
);
export const LeaderboardPage = lazy(() =>
  import('./rewards/ui/LeaderboardPage').then((m) => ({ default: m.LeaderboardPage })),
);

export const GamesListPage = lazy(() =>
  import('./games/ui/GamesListPage').then((m) => ({ default: m.GamesListPage })),
);
export const GameConfigDetailPage = lazy(() =>
  import('./games/ui/GameConfigDetailPage').then((m) => ({ default: m.GameConfigDetailPage })),
);
export const GameConfigEditor = lazy(() =>
  import('./games/ui/GameConfigEditor').then((m) => ({ default: m.GameConfigEditor })),
);
export const StudentGamesPage = lazy(() =>
  import('./games/ui/StudentGamesPage').then((m) => ({ default: m.StudentGamesPage })),
);
export const GamePlayerPage = lazy(() =>
  import('./games/ui/GamePlayerPage').then((m) => ({ default: m.GamePlayerPage })),
);

export const ActivitiesPage = lazy(() =>
  import('./activities/ui/ActivitiesPage').then((m) => ({ default: m.ActivitiesPage })),
);
export const ActivityDetailPage = lazy(() =>
  import('./activities/ui/ActivityDetailPage').then((m) => ({ default: m.ActivityDetailPage })),
);
