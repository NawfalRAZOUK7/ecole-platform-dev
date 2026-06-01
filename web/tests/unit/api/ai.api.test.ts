import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { gamesService } from '@/features/ai/games/api/games.api';
import { rewardsService } from '@/features/ai/rewards/api/rewards.api';
import { activitiesService } from '@/features/ai/activities/api/activities.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

const rawConfig = {
  id: 'game-1',
  game_type: 'memory_match',
  title: 'Memory Game',
  title_ar: null,
  title_fr: null,
  subject: 'Math',
  difficulty: 'easy',
  target_age_min: 5,
  target_age_max: 10,
  config: {},
  reward_stars: 3,
  reward_xp: 10,
  school_id: null,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: null,
};

// ── gamesService ──────────────────────────────────────────────────────────────

describe('gamesService', () => {
  it('listConfigs returns normalized game configs', async () => {
    server.use(
      http.get('/api/v1/games/configs', () =>
        HttpResponse.json({ data: [rawConfig], meta: listMeta }),
      ),
    );
    const result = await gamesService.listConfigs();
    expect(result.items).toHaveLength(1);
    expect(result.items[0].gameType).toBe('memory_match');
    expect(result.nextCursor).toBeNull();
  });

  it('listConfigs with filters passes params', async () => {
    server.use(
      http.get('/api/v1/games/configs', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await gamesService.listConfigs({ difficulty: 'easy', subject: 'Math' });
    expect(result.items).toEqual([]);
  });

  it('getConfig returns normalized single config', async () => {
    server.use(
      http.get('/api/v1/games/configs/game-1', () => HttpResponse.json({ data: rawConfig, meta })),
    );
    const result = await gamesService.getConfig('game-1');
    expect(result.id).toBe('game-1');
    expect(result.rewardStars).toBe(3);
  });

  it('createConfig posts and returns normalized config', async () => {
    server.use(
      http.post('/api/v1/games/configs', () => HttpResponse.json({ data: rawConfig, meta })),
    );
    const result = await gamesService.createConfig({
      gameType: 'memory_match',
      title: 'Memory Game',
      titleAr: null,
      titleFr: null,
      subject: 'Math',
      difficulty: 'easy',
      targetAgeMin: 5,
      targetAgeMax: 10,
      config: {},
      rewardStars: 3,
      rewardXp: 10,
      schoolId: null,
      isActive: true,
    });
    expect(result.id).toBe('game-1');
  });

  it('updateConfig puts and returns normalized config', async () => {
    server.use(
      http.put('/api/v1/games/configs/game-1', () =>
        HttpResponse.json({ data: { ...rawConfig, difficulty: 'medium' }, meta }),
      ),
    );
    const result = await gamesService.updateConfig('game-1', { difficulty: 'medium' });
    expect(result.difficulty).toBe('medium');
  });

  it('completeConfig posts completion', async () => {
    server.use(
      http.post('/api/v1/games/configs/game-1/complete', () =>
        HttpResponse.json({ data: { xpEarned: 15, levelUp: false }, meta }),
      ),
    );
    const result = await gamesService.completeConfig('game-1', { score: 100, timeSeconds: 60 });
    expect(result.xpEarned).toBe(15);
    expect(result.levelUp).toBe(false);
  });
});

// ── rewardsService ────────────────────────────────────────────────────────────

describe('rewardsService', () => {
  const rawRewards = {
    id: 'r-1',
    student_id: 'student-1',
    stars: 50,
    xp: 100,
    level: 3,
    streak_days: 5,
    longest_streak: 10,
    badges: ['badge-1'],
    last_activity_at: null,
    level_progress: 40,
  };

  const rawEvent = {
    id: 'ev-1',
    event_type: 'game_complete',
    stars_earned: 3,
    xp_earned: 10,
    source_type: 'game',
    source_id: 'game-1',
    created_at: new Date().toISOString(),
  };

  const rawLeaderboard = {
    student_id: 'student-1',
    student_name: 'Alice',
    stars: 100,
    level: 5,
    rank: 1,
  };

  const rawBadge = {
    id: 'badge-1',
    code: 'first_game',
    title_fr: 'Premier jeu',
    title_ar: 'أول لعبة',
    title_en: 'First Game',
    description_fr: null,
    description_ar: null,
    description_en: null,
    icon: null,
    criteria_type: 'count',
    criteria_value: 1,
    display_order: 1,
    is_active: true,
  };

  it('getMyRewards returns normalized rewards', async () => {
    server.use(http.get('/api/v1/rewards/me', () => HttpResponse.json({ data: rawRewards, meta })));
    const result = await rewardsService.getMyRewards();
    expect(result.level).toBe(3);
    expect(result.stars).toBe(50);
  });

  it('getStudentRewards returns student rewards', async () => {
    server.use(
      http.get('/api/v1/rewards/student/student-1', () =>
        HttpResponse.json({ data: rawRewards, meta }),
      ),
    );
    const result = await rewardsService.getStudentRewards('student-1');
    expect(result.studentId).toBe('student-1');
  });

  it('getStudentHistory returns reward events', async () => {
    server.use(
      http.get('/api/v1/rewards/student/student-1/history', () =>
        HttpResponse.json({ data: [rawEvent], meta: listMeta }),
      ),
    );
    const result = await rewardsService.getStudentHistory('student-1');
    expect(result).toHaveLength(1);
    expect(result[0].eventType).toBe('game_complete');
  });

  it('getLeaderboard returns leaderboard entries', async () => {
    server.use(
      http.get('/api/v1/rewards/leaderboard/class-1', () =>
        HttpResponse.json({ data: [rawLeaderboard], meta: listMeta }),
      ),
    );
    const result = await rewardsService.getLeaderboard('class-1');
    expect(result).toHaveLength(1);
    expect(result[0].rank).toBe(1);
  });

  it('getBadges returns badge list', async () => {
    server.use(
      http.get('/api/v1/rewards/badges', () =>
        HttpResponse.json({ data: [rawBadge], meta: listMeta }),
      ),
    );
    const result = await rewardsService.getBadges();
    expect(result).toHaveLength(1);
    expect(result[0].code).toBe('first_game');
  });

  it('createBadge posts and returns badge', async () => {
    server.use(
      http.post('/api/v1/rewards/badges', () => HttpResponse.json({ data: rawBadge, meta })),
    );
    const result = await rewardsService.createBadge({
      code: 'first_game',
      titleFr: 'Premier jeu',
      titleAr: 'أول لعبة',
      titleEn: 'First Game',
    });
    expect(result.id).toBe('badge-1');
  });

  it('updateBadge puts badge', async () => {
    server.use(
      http.put('/api/v1/rewards/badges/badge-1', () =>
        HttpResponse.json({ data: { ...rawBadge, is_active: false }, meta }),
      ),
    );
    const result = await rewardsService.updateBadge('badge-1', { isActive: false });
    expect(result.isActive).toBe(false);
  });

  it('awardReward posts and returns result', async () => {
    const awardResponse = {
      reward: rawRewards,
      newly_earned_badges: [],
    };
    server.use(
      http.post('/api/v1/rewards/award', () => HttpResponse.json({ data: awardResponse, meta })),
    );
    const result = await rewardsService.awardReward({
      student_id: 'student-1',
      event_type: 'game_complete',
      stars: 3,
      xp: 10,
    });
    expect(result.reward.level).toBe(3);
    expect(result.newly_earned_badges).toEqual([]);
  });
});

// ── activitiesService ─────────────────────────────────────────────────────────

describe('activitiesService', () => {
  const activity = {
    id: 'act-1',
    title: 'Drag Drop Exercise',
    difficulty: 'easy',
    activity_type: 'drag_drop',
  };

  const session = {
    id: 'session-1',
    activity_id: 'act-1',
    student_id: 'student-1',
    status: 'started',
    score: null,
    attempt_no: 1,
  };

  it('list returns activities', async () => {
    server.use(
      http.get('/api/v1/activities', () => HttpResponse.json({ data: [activity], meta: listMeta })),
    );
    const result = await activitiesService.list();
    expect(result.data).toHaveLength(1);
  });

  it('getDetail finds activity by id', async () => {
    server.use(
      http.get('/api/v1/activities', () => HttpResponse.json({ data: [activity], meta: listMeta })),
    );
    const result = await activitiesService.getDetail('act-1');
    expect(result.data.id).toBe('act-1');
  });

  it('createSession posts session creation', async () => {
    server.use(
      http.post('/api/v1/activities/sessions', () => HttpResponse.json({ data: session, meta })),
    );
    const result = await activitiesService.createSession('act-1');
    expect(result.data.activity_id).toBe('act-1');
  });

  it('completeSession posts session completion', async () => {
    server.use(
      http.post('/api/v1/activities/sessions/session-1/complete', () =>
        HttpResponse.json({ data: { ...session, status: 'completed', score: 85 }, meta }),
      ),
    );
    const result = await activitiesService.completeSession('session-1', 85);
    expect(result.data.status).toBe('completed');
  });
});
