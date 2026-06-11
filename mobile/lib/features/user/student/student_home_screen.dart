/// Student home screen — engagement hub with greeting, XP/level,
/// stat cards, and navigation tiles to content/quizzes/writing.
///
/// Mirrors web StudentHomePage.tsx — mobile-first design for children.
/// API: uses rewards provider (GET /rewards/me) + auth state for user name.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/domain/entities/ai/rewards.dart';
import 'package:ecole_platform/domain/entities/academic/timetable.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/ai/rewards/rewards_provider.dart';
import 'package:ecole_platform/features/academic/timetable/timetable_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class StudentHomeScreen extends ConsumerWidget {
  const StudentHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final authState = ref.watch(authProvider);
    final rewardsAsync = ref.watch(rewardsProvider);
    final timetableState = ref.watch(timetableProvider);
    final t = AppLocalizations.of(ref);
    final isRtl = ref.watch(localeProvider) == 'ar';
    final textDirection = isRtl ? TextDirection.rtl : TextDirection.ltr;
    final user = authState.user;
    final firstName = user?.fullName.split(' ').first ?? '';
    final displayName = firstName.isEmpty ? 'élève' : firstName;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => ref.read(rewardsProvider.notifier).refresh(),
          child: ListView(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.base,
              vertical: AppSpacing.lg,
            ),
            children: [
              Text(
                '👋 ${t.t('studentHome.greeting').replaceAll('{name}', displayName)}',
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: theme.colorScheme.primary,
                ),
                textDirection: textDirection,
              ),
              const SizedBox(height: AppSpacing.xs),
              Text(
                t.t('studentHome.subtitle'),
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                textDirection: textDirection,
              ),
              const SizedBox(height: AppSpacing.lg),
              rewardsAsync.when(
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(AppSpacing.lg),
                    child: CircularProgressIndicator(),
                  ),
                ),
                error: (_, __) => _ErrorCard(
                  message: t.t('studentHome.loadError'),
                  retryLabel: t.t('common.retry'),
                  onRetry: () => ref.read(rewardsProvider.notifier).refresh(),
                ),
                data: (rewards) => Column(
                  children: [
                    _StatCardsGrid(rewards: rewards, t: t),
                    const SizedBox(height: AppSpacing.lg),
                    if (rewards.badges.isNotEmpty) ...[
                      _BadgesPreview(
                        badges: rewards.badges,
                        title: t.t('studentHome.myBadges'),
                      ),
                      const SizedBox(height: AppSpacing.lg),
                    ],
                  ],
                ),
              ),
              _SectionTitle(
                emoji: '🚀',
                title: t.t('studentHome.startLearning'),
              ),
              const SizedBox(height: AppSpacing.md),
              _CtaRow(
                items: [
                  _CtaItem(
                    emoji: '📚',
                    label: t.t('studentHome.lessons'),
                    path: '/student/content',
                    colors: const [
                      Color(0xFF7C3AED),
                      Color(0xFFA78BFA),
                    ],
                    textColor: Colors.white,
                  ),
                  _CtaItem(
                    emoji: '📝',
                    label: t.t('studentHome.quizzes'),
                    path: '/student/quizzes',
                    colors: const [
                      Color(0xFFF59E0B),
                      Color(0xFFFCD34D),
                    ],
                    textColor: const Color(0xFF7C2D12),
                  ),
                  _CtaItem(
                    emoji: '✏️',
                    label: t.t('studentHome.writing'),
                    path: '/student/writing',
                    colors: const [
                      Color(0xFF10B981),
                      Color(0xFF34D399),
                    ],
                    textColor: Colors.white,
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.lg),
              _SectionTitle(
                emoji: '⚡',
                title: t.t('studentHome.quickAccess'),
              ),
              const SizedBox(height: AppSpacing.md),
              _QuickLinksGrid(
                links: [
                  _QuickLink(
                    emoji: '📊',
                    label: t.t('studentHome.myProgress'),
                    path: '/progress',
                  ),
                  _QuickLink(
                    emoji: '🏆',
                    label: t.t('studentHome.myRewards'),
                    path: '/rewards',
                  ),
                  _QuickLink(
                    emoji: '🎯',
                    label: t.t('studentHome.skills'),
                    path: '/skills',
                  ),
                  _QuickLink(
                    emoji: '📢',
                    label: t.t('studentHome.news'),
                    path: '/announcements',
                  ),
                  _QuickLink(
                    emoji: '🗓️',
                    label: t.t('studentHome.calendar'),
                    path: '/calendar',
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.lg),
              _TodayScheduleSection(
                timetableState: timetableState,
                title: t.t('studentHome.todaySchedule'),
              ),
              const SizedBox(height: AppSpacing.xl),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Stat cards (XP, Stars, Streak, Level) ──

class _StatCardsGrid extends StatelessWidget {
  final StudentRewards rewards;
  final AppLocalizations t;

  const _StatCardsGrid({
    required this.rewards,
    required this.t,
  });

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: AppSpacing.md,
      crossAxisSpacing: AppSpacing.md,
      childAspectRatio: 1.22,
      children: [
        _MiniStatCard(
          emoji: '✨',
          value: '${rewards.xp}',
          label: 'XP',
          valueColor: AppColors.primary,
        ),
        _MiniStatCard(
          emoji: '⭐',
          value: '${rewards.stars}',
          label: t.t('studentHome.stars'),
          valueColor: AppColors.accent,
        ),
        _MiniStatCard(
          emoji: '🔥',
          value: '${rewards.streakDays}',
          label: t.t('studentHome.days'),
          valueColor: const Color(0xFFF97316),
        ),
        _MiniStatCard(
          emoji: '🏅',
          value: '${rewards.level}',
          label: t.t('studentHome.level'),
          valueColor: AppColors.secondary,
          progress: rewards.levelProgress,
        ),
      ],
    );
  }
}

class _MiniStatCard extends StatelessWidget {
  final String emoji;
  final String value;
  final String label;
  final Color valueColor;
  final double? progress;

  const _MiniStatCard({
    required this.emoji,
    required this.value,
    required this.label,
    required this.valueColor,
    this.progress,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.md,
        horizontal: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border, width: 2),
        boxShadow: const [
          BoxShadow(
            color: Color(0x11000000),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 30)),
          const SizedBox(height: AppSpacing.xs),
          Text(
            value,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w800,
              color: valueColor,
            ),
          ),
          Text(
            label,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          if (progress != null) ...[
            const SizedBox(height: AppSpacing.sm),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                value: progress!.clamp(0, 1),
                minHeight: 8,
                backgroundColor: const Color(0xFFE9D5FF),
                valueColor: const AlwaysStoppedAnimation<Color>(
                  AppColors.secondary,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ── CTA row matching web StudentHomePage ──

class _CtaItem {
  final String emoji;
  final String label;
  final String path;
  final List<Color> colors;
  final Color textColor;

  const _CtaItem({
    required this.emoji,
    required this.label,
    required this.path,
    required this.colors,
    required this.textColor,
  });
}

class _CtaRow extends StatelessWidget {
  final List<_CtaItem> items;

  const _CtaRow({required this.items});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: items.map((item) {
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: Material(
            color: Colors.transparent,
            borderRadius: BorderRadius.circular(18),
            child: InkWell(
              borderRadius: BorderRadius.circular(18),
              onTap: () => GoRouter.of(context).go(item.path),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  vertical: AppSpacing.md,
                  horizontal: AppSpacing.lg,
                ),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(18),
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: item.colors,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: item.colors.first.withAlpha(65),
                      blurRadius: 14,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(item.emoji, style: const TextStyle(fontSize: 24)),
                    const SizedBox(width: AppSpacing.sm),
                    Flexible(
                      child: Text(
                        item.label,
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: item.textColor,
                          fontWeight: FontWeight.w800,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

class _BadgesPreview extends StatelessWidget {
  final List<String> badges;
  final String title;

  const _BadgesPreview({
    required this.badges,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionTitle(
          emoji: '🏅',
          title: title,
        ),
        const SizedBox(height: AppSpacing.sm),
        Wrap(
          spacing: AppSpacing.sm,
          runSpacing: AppSpacing.sm,
          children: badges.take(6).map((badge) {
            return Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: AppSpacing.sm,
              ),
              decoration: BoxDecoration(
                color: KidsContentColors.levelBadge.withAlpha(20),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: KidsContentColors.levelBadge.withAlpha(60),
                ),
              ),
              child: Text(
                '🎖️ $badge',
                style: theme.textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: KidsContentColors.levelBadge,
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }
}

// ── Section title ──

class _SectionTitle extends StatelessWidget {
  final String emoji;
  final String title;

  const _SectionTitle({
    required this.emoji,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 20)),
        const SizedBox(width: AppSpacing.sm),
        Text(
          title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
            color: KidsContentColors.storyText,
          ),
        ),
      ],
    );
  }
}

// ── Quick links grid ──

class _QuickLink {
  final String emoji;
  final String label;
  final String path;

  const _QuickLink({
    required this.emoji,
    required this.label,
    required this.path,
  });
}

class _QuickLinksGrid extends StatelessWidget {
  final List<_QuickLink> links;

  const _QuickLinksGrid({required this.links});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return GridView.count(
      crossAxisCount: 3,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: AppSpacing.sm,
      crossAxisSpacing: AppSpacing.sm,
      childAspectRatio: 1.15,
      children: links.map((link) {
        return Material(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: () => GoRouter.of(context).go(link.path),
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.sm,
                vertical: AppSpacing.md,
              ),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border, width: 2),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    link.emoji,
                    style: const TextStyle(fontSize: 26),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    link.label,
                    style: theme.textTheme.bodySmall?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: AppColors.text,
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ── Error card with retry ──

class _ErrorCard extends StatelessWidget {
  final String message;
  final String retryLabel;
  final VoidCallback onRetry;

  const _ErrorCard({
    required this.message,
    required this.retryLabel,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppColors.error.withAlpha(15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.error.withAlpha(60)),
      ),
      child: Column(
        children: [
          Text(
            message,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: AppColors.error,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          TextButton(
            onPressed: onRetry,
            child: Text(retryLabel),
          ),
        ],
      ),
    );
  }
}

// ── Today's schedule section ──

class _TodayScheduleSection extends StatelessWidget {
  final TimetableState timetableState;
  final String title;

  const _TodayScheduleSection({
    required this.timetableState,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    final today = DateTime.now().weekday;

    if (timetableState.isLoading) {
      return const SizedBox(
        height: 60,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (timetableState.error != null) {
      return const SizedBox.shrink();
    }

    final schedule = timetableState.schedule;
    if (schedule == null || schedule.slots.isEmpty) {
      return const SizedBox.shrink();
    }

    // Filter slots for today
    final todaySlots = schedule.slots
        .where((slot) => slot.dayOfWeek == today)
        .toList()
      ..sort((a, b) => a.startTime.compareTo(b.startTime));

    if (todaySlots.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionTitle(
          emoji: '📅',
          title: title,
        ),
        const SizedBox(height: AppSpacing.sm),
        ...todaySlots.map((slot) => _ScheduleSlotCard(slot: slot)),
      ],
    );
  }
}

class _ScheduleSlotCard extends StatelessWidget {
  final TimetableSlot slot;

  const _ScheduleSlotCard({required this.slot});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.sm,
              vertical: AppSpacing.xs,
            ),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              slot.startTime.substring(0, 5),
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: theme.colorScheme.onPrimaryContainer,
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  slot.subject,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (slot.room != null)
                  Text(
                    slot.room!,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
