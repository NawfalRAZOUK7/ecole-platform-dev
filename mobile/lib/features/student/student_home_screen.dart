/// Student home screen — engagement hub with greeting, XP/level,
/// stat cards, and navigation tiles to content/quizzes/games/writing.
///
/// Mirrors web StudentHomePage.tsx — mobile-first design for children.
/// API: uses rewards provider (GET /rewards/me) + auth state for user name.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/rewards/rewards_provider.dart';
import 'package:ecole_platform/features/rewards/widgets/level_badge.dart';
import 'package:ecole_platform/features/rewards/widgets/streak_card.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class StudentHomeScreen extends ConsumerWidget {
  const StudentHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final authState = ref.watch(authProvider);
    final rewardsAsync = ref.watch(rewardsProvider);
    final user = authState.user;
    final firstName = user?.fullName.split(' ').first ?? '';

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => ref.read(rewardsProvider.notifier).refresh(),
          child: ListView(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.base,
              vertical: AppSpacing.lg,
            ),
            children: [
              // ── Greeting ──
              Text(
                'مرحبا، $firstName! 👋',
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: KidsContentColors.storyText,
                ),
                textDirection: TextDirection.rtl,
              ),
              const SizedBox(height: AppSpacing.xs),
              Text(
                'هيّا نتعلم اليوم!',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                textDirection: TextDirection.rtl,
              ),
              const SizedBox(height: AppSpacing.lg),

              // ── Level badge + XP progress ──
              rewardsAsync.when(
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(AppSpacing.lg),
                    child: CircularProgressIndicator(),
                  ),
                ),
                error: (_, __) => _ErrorCard(
                  onRetry: () =>
                      ref.read(rewardsProvider.notifier).refresh(),
                ),
                data: (rewards) => Column(
                  children: [
                    LevelBadge(rewards: rewards),
                    const SizedBox(height: AppSpacing.base),

                    // ── Stat cards row ──
                    _StatCardsRow(rewards: rewards),
                    const SizedBox(height: AppSpacing.base),

                    // ── Streak card ──
                    StreakCard(rewards: rewards),
                    const SizedBox(height: AppSpacing.lg),

                    // ── Badges preview ──
                    if (rewards.badges.isNotEmpty) ...[
                      _BadgesPreview(badges: rewards.badges),
                      const SizedBox(height: AppSpacing.lg),
                    ],
                  ],
                ),
              ),

              // ── CTA: Ready to learn? ──
              _SectionTitle(
                emoji: '🚀',
                title: 'ابدأ التعلم',
                textDirection: TextDirection.rtl,
              ),
              const SizedBox(height: AppSpacing.md),
              _CtaGrid(
                items: const [
                  _CtaItem(
                    emoji: '📚',
                    label: 'الدروس',
                    sublabel: 'تعلّم',
                    path: '/student/content',
                    color: Color(0xFFEFF6FF),
                    borderColor: Color(0xFF93C5FD),
                  ),
                  _CtaItem(
                    emoji: '📝',
                    label: 'الاختبارات',
                    sublabel: 'أجب',
                    path: '/student/quizzes',
                    color: Color(0xFFFEF3C7),
                    borderColor: Color(0xFFFBBF24),
                  ),
                  _CtaItem(
                    emoji: '✏️',
                    label: 'الكتابة',
                    sublabel: 'اكتب قصة',
                    path: '/student/writing',
                    color: Color(0xFFF0FDF4),
                    borderColor: Color(0xFF86EFAC),
                  ),
                  _CtaItem(
                    emoji: '🎮',
                    label: 'الألعاب',
                    sublabel: 'العب وتعلّم',
                    path: '/games/memory',
                    color: Color(0xFFFAF5FF),
                    borderColor: Color(0xFFC4B5FD),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.lg),

              // ── Quick links ──
              _SectionTitle(
                emoji: '⚡',
                title: 'الوصول السريع',
                textDirection: TextDirection.rtl,
              ),
              const SizedBox(height: AppSpacing.md),
              _QuickLinksRow(
                links: const [
                  _QuickLink(emoji: '📊', label: 'تقدّمي', path: '/progress'),
                  _QuickLink(emoji: '🏆', label: 'جوائزي', path: '/rewards'),
                  _QuickLink(emoji: '🎨', label: 'تلوين', path: '/coloring'),
                  _QuickLink(emoji: '📢', label: 'أخبار', path: '/announcements'),
                  _QuickLink(emoji: '🗓️', label: 'التقويم', path: '/calendar'),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Stat cards (XP, Stars, Streak) ──

class _StatCardsRow extends StatelessWidget {
  final StudentRewards rewards;

  const _StatCardsRow({required this.rewards});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _MiniStatCard(
            emoji: '✨',
            value: '${rewards.xp}',
            label: 'XP',
            color: KidsContentColors.xpBar,
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: _MiniStatCard(
            emoji: '⭐',
            value: '${rewards.stars}',
            label: 'نجوم',
            color: KidsContentColors.starGold,
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: _MiniStatCard(
            emoji: '🔥',
            value: '${rewards.streakDays}',
            label: 'أيام',
            color: KidsContentColors.streakOrange,
          ),
        ),
      ],
    );
  }
}

class _MiniStatCard extends StatelessWidget {
  final String emoji;
  final String value;
  final String label;
  final Color color;

  const _MiniStatCard({
    required this.emoji,
    required this.value,
    required this.label,
    required this.color,
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
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withAlpha(70)),
      ),
      child: Column(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 22)),
          const SizedBox(height: AppSpacing.xs),
          Text(
            value,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w800,
              color: KidsContentColors.storyText,
            ),
          ),
          Text(
            label,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
            textDirection: TextDirection.rtl,
          ),
        ],
      ),
    );
  }
}

// ── Badges preview ──

class _BadgesPreview extends StatelessWidget {
  final List<String> badges;

  const _BadgesPreview({required this.badges});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionTitle(
          emoji: '🏅',
          title: 'شاراتي',
          textDirection: TextDirection.rtl,
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
  final TextDirection textDirection;

  const _SectionTitle({
    required this.emoji,
    required this.title,
    this.textDirection = TextDirection.ltr,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      textDirection: textDirection,
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

// ── CTA grid (learn, quiz, write, play) ──

class _CtaItem {
  final String emoji;
  final String label;
  final String sublabel;
  final String path;
  final Color color;
  final Color borderColor;

  const _CtaItem({
    required this.emoji,
    required this.label,
    required this.sublabel,
    required this.path,
    required this.color,
    required this.borderColor,
  });
}

class _CtaGrid extends StatelessWidget {
  final List<_CtaItem> items;

  const _CtaGrid({required this.items});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: AppSpacing.md,
      crossAxisSpacing: AppSpacing.md,
      childAspectRatio: 1.4,
      children: items.map((item) {
        return Material(
          color: item.color,
          borderRadius: BorderRadius.circular(22),
          child: InkWell(
            borderRadius: BorderRadius.circular(22),
            onTap: () => GoRouter.of(context).go(item.path),
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: item.borderColor, width: 1.5),
              ),
              padding: const EdgeInsets.all(AppSpacing.base),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(item.emoji, style: const TextStyle(fontSize: 32)),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    item.label,
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                      color: KidsContentColors.storyText,
                    ),
                    textDirection: TextDirection.rtl,
                  ),
                  Text(
                    item.sublabel,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: KidsContentColors.storyText.withAlpha(160),
                    ),
                    textDirection: TextDirection.rtl,
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

// ── Quick links row ──

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

class _QuickLinksRow extends StatelessWidget {
  final List<_QuickLink> links;

  const _QuickLinksRow({required this.links});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SizedBox(
      height: 90,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        reverse: true, // RTL: scroll starts from right
        itemCount: links.length,
        separatorBuilder: (_, __) => const SizedBox(width: AppSpacing.md),
        itemBuilder: (context, index) {
          final link = links[index];
          return GestureDetector(
            onTap: () => GoRouter.of(context).go(link.path),
            child: SizedBox(
              width: 72,
              child: Column(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: Center(
                      child: Text(
                        link.emoji,
                        style: const TextStyle(fontSize: 26),
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    link.label,
                    style: theme.textTheme.bodySmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textDirection: TextDirection.rtl,
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

// ── Error card with retry ──

class _ErrorCard extends StatelessWidget {
  final VoidCallback onRetry;

  const _ErrorCard({required this.onRetry});

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
            'تعذّر تحميل البيانات',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: AppColors.error,
              fontWeight: FontWeight.w600,
            ),
            textDirection: TextDirection.rtl,
          ),
          const SizedBox(height: AppSpacing.sm),
          TextButton(
            onPressed: onRetry,
            child: const Text('إعادة المحاولة'),
          ),
        ],
      ),
    );
  }
}
