/// Writing Workspace screen — student writes text and receives AI feedback.
///
/// Phase A2: Mirrors web WritingWorkspacePage.tsx.
/// API: POST /api/v1/writing-attempts via writing_provider.dart.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'writing_provider.dart';

const _writingTypes = ['story', 'essay', 'letter', 'description', 'free'];
const _minChars = 20;
const _maxChars = 5000;

const _writingTypeLabels = {
  'story': 'قصة',
  'essay': 'مقال',
  'letter': 'رسالة',
  'description': 'وصف',
  'free': 'حر',
};

class WritingWorkspaceScreen extends ConsumerStatefulWidget {
  const WritingWorkspaceScreen({super.key});

  @override
  ConsumerState<WritingWorkspaceScreen> createState() =>
      _WritingWorkspaceScreenState();
}

class _WritingWorkspaceScreenState
    extends ConsumerState<WritingWorkspaceScreen> {
  final _controller = TextEditingController();
  String _writingType = 'free';

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final text = _controller.text.trim();
    if (text.length < _minChars || text.length > _maxChars) return;
    ref.read(writingProvider.notifier).submit(
          text: text,
          writingType: _writingType,
        );
  }

  void _reset() {
    _controller.clear();
    ref.read(writingProvider.notifier).reset();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(writingProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('✏️ ورشة الكتابة'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: state.result != null
            ? _ResultView(
                result: state.result!,
                originalText: _controller.text,
                onTryAgain: _reset,
                onGoHome: () => context.go('/student/content'),
              )
            : _EditorView(
                controller: _controller,
                writingType: _writingType,
                isLoading: state.isLoading,
                error: state.error,
                onTypeChanged: (t) => setState(() => _writingType = t),
                onSubmit: _submit,
              ),
      ),
    );
  }
}

// ── Editor View ──

class _EditorView extends StatelessWidget {
  const _EditorView({
    required this.controller,
    required this.writingType,
    required this.isLoading,
    required this.error,
    required this.onTypeChanged,
    required this.onSubmit,
  });

  final TextEditingController controller;
  final String writingType;
  final bool isLoading;
  final String? error;
  final ValueChanged<String> onTypeChanged;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'ماذا تكتب؟',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
          ),
          const SizedBox(height: AppSpacing.sm),

          // Writing type chips
          Wrap(
            spacing: AppSpacing.sm,
            runSpacing: AppSpacing.xs,
            children: _writingTypes.map((type) {
              final selected = type == writingType;
              return ChoiceChip(
                label: Text(_writingTypeLabels[type] ?? type),
                selected: selected,
                onSelected: (_) => onTypeChanged(type),
                selectedColor: AppColors.primary.withOpacity(0.15),
                labelStyle: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: selected ? AppColors.primary : AppColors.text,
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: AppSpacing.md),

          // Text area
          Expanded(
            child: ValueListenableBuilder<TextEditingValue>(
              valueListenable: controller,
              builder: (context, value, child) {
                return TextField(
                  controller: controller,
                  maxLines: null,
                  expands: true,
                  textAlignVertical: TextAlignVertical.top,
                  textDirection: TextDirection.rtl,
                  maxLength: _maxChars,
                  decoration: InputDecoration(
                    hintText: 'ابدأ الكتابة هنا...',
                    hintTextDirection: TextDirection.rtl,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    counterText:
                        '${value.text.length} / $_maxChars${value.text.length < _minChars ? ' (${_minChars - value.text.length} حرف إضافي مطلوب)' : ''}',
                  ),
                  style: const TextStyle(
                    fontSize: 16,
                    height: 1.7,
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: AppSpacing.md),

          // Error message
          if (error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: Text(
                'حدث خطأ. يرجى المحاولة مرة أخرى.',
                style: TextStyle(color: AppColors.error, fontSize: 13),
                textAlign: TextAlign.center,
              ),
            ),

          // Submit button
          ValueListenableBuilder<TextEditingValue>(
            valueListenable: controller,
            builder: (context, value, _) {
              final canSubmit =
                  value.text.length >= _minChars && !isLoading;
              return FilledButton.icon(
                onPressed: canSubmit ? onSubmit : null,
                icon: isLoading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('🔍'),
                label: Text(isLoading ? 'جاري الفحص...' : 'راجع كتابتي'),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}

// ── Result View ──

class _ResultView extends StatelessWidget {
  const _ResultView({
    required this.result,
    required this.originalText,
    required this.onTryAgain,
    required this.onGoHome,
  });

  final WritingAttemptResponse result;
  final String originalText;
  final VoidCallback onTryAgain;
  final VoidCallback onGoHome;

  @override
  Widget build(BuildContext context) {
    final feedback = result.feedback;
    final theme = Theme.of(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Encouragement banner
          Card(
            color: AppColors.successContainer,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                children: [
                  Text(
                    feedback.score != null && feedback.score! >= 80
                        ? '🎉'
                        : feedback.score != null && feedback.score! >= 50
                            ? '👍'
                            : '💪',
                    style: const TextStyle(fontSize: 48),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    feedback.encouragement.isNotEmpty
                        ? feedback.encouragement
                        : 'أحسنت!',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: AppColors.success,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  if (feedback.score != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      'النتيجة: ${feedback.score}/100',
                      style: TextStyle(
                        fontSize: 13,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.md),

          // Corrected text
          if (feedback.correctedText.isNotEmpty &&
              feedback.correctedText != originalText) ...[
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
                      'النسخة المصححة',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        feedback.correctedText,
                        textDirection: TextDirection.rtl,
                        style: const TextStyle(fontSize: 15, height: 1.7),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.md),
          ],

          // Suggestions
          if (feedback.suggestions.isNotEmpty) ...[
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
                      'نصائح للتحسين',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    ...feedback.suggestions.map(
                      (s) => Padding(
                        padding:
                            const EdgeInsets.only(bottom: AppSpacing.sm),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('• ',
                                style: TextStyle(fontSize: 15)),
                            Expanded(
                              child: Text(
                                s,
                                textDirection: TextDirection.rtl,
                                style: const TextStyle(
                                    fontSize: 14, height: 1.5),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.md),
          ],

          // Actions
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: onTryAgain,
                  icon: const Text('✏️'),
                  label: const Text('اكتب مجدداً'),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onGoHome,
                  icon: const Text('🏠'),
                  label: const Text('الرجوع'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
