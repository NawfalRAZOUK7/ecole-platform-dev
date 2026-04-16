# École Platform — Web App

React 18 + TypeScript + Vite frontend for the École Platform back office and browser-based learner experience.

## Setup

```bash
npm install
npm run dev
```

Useful checks:

```bash
npm run typecheck
npm run lint
npm run test
npm run test:e2e
npm run build
```

## New Pages and Flows

### Rewards viewing

- Student self-view: `/rewards`
- Parent/teacher student view: `/students/:id/rewards`
- Class leaderboard: `/classes/:classId/leaderboard`

The rewards UI includes stars, XP progress, levels, streaks, badge shelves, recent reward history, and leaderboard navigation.

### Teacher game management

- List and filters: `/teacher/games`
- Create: `/teacher/games/new`
- Detail and edit: `/teacher/games/:id`

Teachers and admins can manage memory match, sorting, and vocabulary game configurations with dynamic editors and reward settings.

### Admin badge management

- Badge admin page: `/admin/badges`

Admins can create, edit, reorder, and toggle reward badges, including localized titles/descriptions and icon input/upload.

### Story and coloring CMS

- CMS library: `/cms`
- Upload: `/cms/upload`
- Edit: `/cms/content/:contentId/edit`

CMS now supports `story` and `coloring_book` content types with story-specific metadata fields, page management through `StoryPagesEditor`, and browser-accessible story/coloring views for students.

### Student story and coloring viewers

- Story viewer: `/student/content/:id/read`
- Coloring viewer: `/student/content/:id/color`

The web app provides a page-based story reader and a non-interactive coloring viewer with a mobile-app handoff note.

## Internationalization

All user-facing strings for games, rewards, admin badges, student story/coloring viewers, and CMS story fields are localized in:

- `src/shared/i18n/locales/en.json`
- `src/shared/i18n/locales/fr.json`
- `src/shared/i18n/locales/ar.json`

## End-to-End Coverage

Playwright specs cover the new browser flows:

- `e2e/rewards.spec.ts`
- `e2e/games-management.spec.ts`
- `e2e/cms-story-content.spec.ts`
- `e2e/admin-badges.spec.ts`
