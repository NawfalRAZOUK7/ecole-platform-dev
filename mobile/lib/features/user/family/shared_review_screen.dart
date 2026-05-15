/// Shared review screen — parent views child's learning sessions + adds comments.
///
/// Phase B1: Mirrors web SharedReviewPage.tsx + ReviewDetailPage.tsx.
/// Shows a list of sessions, tapping one opens the detail with comments.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'shared_review_provider.dart';

/// Session list screen for a specific child.
class SharedReviewScreen extends ConsumerStatefulWidget {
  final String childId;

  const SharedReviewScreen({super.key, required this.childId});

  @override
  ConsumerState<SharedReviewScreen> createState() => _SharedReviewScreenState();
}

class _SharedReviewScreenState extends ConsumerState<SharedReviewScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(sharedReviewProvider.notifier).loadSessions(widget.childId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(sharedReviewProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('مراجعة التعلم'),
        centerTitle: true,
      ),
      body: state.isLoading
          ? const Center(child: CircularProgressIndicator())
          : state.error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline, size: 48),
                      const SizedBox(height: 8),
                      Text(
                        'حدث خطأ',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      TextButton(
                        onPressed: () => ref
                            .read(sharedReviewProvider.notifier)
                            .loadSessions(widget.childId),
                        child: const Text('إعادة المحاولة'),
                      ),
                    ],
                  ),
                )
              : state.sessions.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('📭', style: TextStyle(fontSize: 48)),
                          SizedBox(height: 8),
                          Text('لا توجد جلسات تعلم بعد'),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.all(AppSpacing.md),
                      itemCount: state.sessions.length,
                      separatorBuilder: (_, __) =>
                          const SizedBox(height: AppSpacing.sm),
                      itemBuilder: (context, index) {
                        final session = state.sessions[index];
                        return _SessionTile(
                          session: session,
                          onTap: () => context.push(
                            '/family/review/${widget.childId}/sessions/${session.id}',
                          ),
                        );
                      },
                    ),
    );
  }
}

/// Detail screen for a specific session with comment form.
class SharedReviewDetailScreen extends ConsumerStatefulWidget {
  final String childId;
  final String sessionId;

  const SharedReviewDetailScreen({
    super.key,
    required this.childId,
    required this.sessionId,
  });

  @override
  ConsumerState<SharedReviewDetailScreen> createState() =>
      _SharedReviewDetailScreenState();
}

class _SharedReviewDetailScreenState
    extends ConsumerState<SharedReviewDetailScreen> {
  final _commentController = TextEditingController();
  String? _selectedEmoji;

  static const _emojis = ['👏', '🌟', '💪', '❤️', '🎉', '🏆'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref
          .read(sharedReviewProvider.notifier)
          .loadDetail(widget.childId, widget.sessionId);
    });
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  void _submit() {
    final text = _commentController.text.trim();
    if (text.isEmpty) return;
    ref.read(sharedReviewProvider.notifier).addComment(
          widget.childId,
          widget.sessionId,
          text: text,
          emoji: _selectedEmoji,
        );
    _commentController.clear();
    setState(() => _selectedEmoji = null);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(sharedReviewProvider);
    final detail = state.detail;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(detail?.title ?? 'تفاصيل الجلسة')),
      body: state.isLoading || detail == null
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Session info card
                  Card(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(AppSpacing.md),
                      child: Wrap(
                        spacing: 20,
                        runSpacing: 10,
                        children: [
                          _InfoChip('النوع', detail.type),
                          _InfoChip('الحالة', detail.status),
                          if (detail.score != null)
                            _InfoChip(
                              'النتيجة',
                              '${detail.score!.toStringAsFixed(0)}${detail.maxScore != null ? "/${detail.maxScore}" : "/100"}',
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),

                  // Writing text if applicable
                  if (detail.type == 'writing' && detail.text != null) ...[
                    Card(
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'نص الطفل',
                              style: theme.textTheme.titleSmall
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(height: 8),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: AppColors.surface,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                detail.text!,
                                textDirection: TextDirection.rtl,
                                style: const TextStyle(
                                  fontSize: 15,
                                  height: 1.7,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                  ],

                  // Comments section
                  Card(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(AppSpacing.md),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'التشجيعات (${detail.comments.length})',
                            style: theme.textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                              color: AppColors.primary,
                            ),
                          ),
                          const SizedBox(height: AppSpacing.sm),

                          if (detail.comments.isEmpty)
                            const Padding(
                              padding: EdgeInsets.only(bottom: 12),
                              child: Text(
                                'لا توجد تعليقات بعد. كن أول من يشجع!',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.grey,
                                ),
                              ),
                            ),

                          ...detail.comments.map(
                            (c) => Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: AppColors.surface,
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        if (c.emoji != null)
                                          Padding(
                                            padding: const EdgeInsets.only(
                                              right: 6,
                                            ),
                                            child: Text(
                                              c.emoji!,
                                              style: const TextStyle(
                                                fontSize: 18,
                                              ),
                                            ),
                                          ),
                                        Expanded(
                                          child: Text(
                                            c.text,
                                            style: const TextStyle(
                                              fontSize: 14,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(height: AppSpacing.sm),

                          // Emoji picker
                          Wrap(
                            spacing: 6,
                            children: _emojis.map((e) {
                              final selected = e == _selectedEmoji;
                              return GestureDetector(
                                onTap: () => setState(
                                  () => _selectedEmoji = selected ? null : e,
                                ),
                                child: Container(
                                  width: 36,
                                  height: 36,
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(10),
                                    border: Border.all(
                                      color: selected
                                          ? AppColors.primary
                                          : AppColors.border,
                                      width: 2,
                                    ),
                                    color: selected
                                        ? AppColors.primary
                                            .withValues(alpha: 0.1)
                                        : null,
                                  ),
                                  alignment: Alignment.center,
                                  child: Text(
                                    e,
                                    style: const TextStyle(
                                      fontSize: 18,
                                    ),
                                  ),
                                ),
                              );
                            }).toList(),
                          ),
                          const SizedBox(height: 8),

                          // Comment input
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: _commentController,
                                  decoration: InputDecoration(
                                    hintText: 'اكتب تشجيعاً...',
                                    border: OutlineInputBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    contentPadding: const EdgeInsets.symmetric(
                                      horizontal: 14,
                                      vertical: 10,
                                    ),
                                  ),
                                  maxLength: 1000,
                                  onSubmitted: (_) => _submit(),
                                ),
                              ),
                              const SizedBox(width: 8),
                              FilledButton(
                                onPressed: state.isPosting ? null : _submit,
                                style: FilledButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 16,
                                    vertical: 14,
                                  ),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                ),
                                child: state.isPosting
                                    ? const SizedBox(
                                        width: 18,
                                        height: 18,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          color: Colors.white,
                                        ),
                                      )
                                    : const Text('إرسال'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

// ── Helper widgets ──

class _SessionTile extends StatelessWidget {
  final ReviewSession session;
  final VoidCallback onTap;

  const _SessionTile({required this.session, required this.onTap});

  static const _typeIcons = {
    'quiz': Icons.quiz_outlined,
    'content': Icons.menu_book_outlined,
    'writing': Icons.edit_note_outlined,
    'activity': Icons.sports_esports_outlined,
  };

  static const _typeColors = {
    'quiz': AppColors.primary,
    'content': AppColors.info,
    'writing': AppColors.success,
    'activity': AppColors.warning,
  };

  @override
  Widget build(BuildContext context) {
    final color = _typeColors[session.type] ?? AppColors.primary;
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _typeIcons[session.type] ?? Icons.assignment,
                  color: color,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      session.title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (session.startedAt != null)
                      Text(
                        _formatDate(session.startedAt!),
                        style: const TextStyle(
                          fontSize: 12,
                          color: Colors.grey,
                        ),
                      ),
                  ],
                ),
              ),
              if (session.score != null)
                Text(
                  '${session.score!.toStringAsFixed(0)}${session.maxScore != null ? "/${session.maxScore}" : "%"}',
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                    color: _scoreColor(session.score),
                  ),
                ),
              const SizedBox(width: 4),
              const Icon(Icons.chevron_right, color: Colors.grey),
            ],
          ),
        ),
      ),
    );
  }

  Color _scoreColor(double? score) {
    if (score == null) return Colors.grey;
    if (score >= 80) return AppColors.success;
    if (score >= 50) return AppColors.warning;
    return AppColors.error;
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso);
      return '${dt.day}/${dt.month} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }
}

class _InfoChip extends StatelessWidget {
  final String label;
  final String value;

  const _InfoChip(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: Colors.grey,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }
}
