/// Teacher submissions screen — view/grade student submissions.
///
/// Reference: Phase 5B (from 4B)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';

// ── State ──

class _SubmissionsState {
  final List<Submission> items;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final String? statusFilter;
  final String? gradingId;
  final Set<String> actionLoading;

  const _SubmissionsState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.statusFilter,
    this.gradingId,
    this.actionLoading = const {},
  });

  _SubmissionsState copyWith({
    List<Submission>? items,
    bool? isLoading,
    bool? isLoadingMore,
    String? error,
    bool clearError = false,
    String? nextCursor,
    bool? hasMore,
    String? statusFilter,
    bool clearStatusFilter = false,
    String? gradingId,
    bool clearGradingId = false,
    Set<String>? actionLoading,
  }) {
    return _SubmissionsState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      error: clearError ? null : (error ?? this.error),
      nextCursor: nextCursor ?? this.nextCursor,
      hasMore: hasMore ?? this.hasMore,
      statusFilter:
          clearStatusFilter ? null : (statusFilter ?? this.statusFilter),
      gradingId: clearGradingId ? null : (gradingId ?? this.gradingId),
      actionLoading: actionLoading ?? this.actionLoading,
    );
  }
}

class _SubmissionsNotifier extends StateNotifier<_SubmissionsState> {
  final Ref _ref;

  _SubmissionsNotifier(this._ref)
      : super(const _SubmissionsState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final repo = _ref.read(teacherRepositoryProvider);
      final result = await repo.getSubmissions(status: state.statusFilter);
      state = state.copyWith(
        items: result.items,
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || !state.hasMore) return;
    state = state.copyWith(isLoadingMore: true);
    try {
      final repo = _ref.read(teacherRepositoryProvider);
      final result = await repo.getSubmissions(
        cursor: state.nextCursor,
        status: state.statusFilter,
      );
      state = state.copyWith(
        items: [...state.items, ...result.items],
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        isLoadingMore: false,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: e.toString());
    }
  }

  void setStatusFilter(String? v) {
    state = v == null
        ? state.copyWith(clearStatusFilter: true)
        : state.copyWith(statusFilter: v);
    load();
  }

  void toggleGrading(String id) {
    state = state.gradingId == id
        ? state.copyWith(clearGradingId: true)
        : state.copyWith(gradingId: id);
  }

  Future<void> gradeSubmission(
    String id, {
    required double score,
    String? feedbackText,
    bool publish = true,
  }) async {
    state = state.copyWith(actionLoading: {...state.actionLoading, id});
    try {
      final repo = _ref.read(teacherRepositoryProvider);
      await repo.gradeSubmission(id,
          score: score, feedbackText: feedbackText, publish: publish);
      state = state.copyWith(clearGradingId: true);
      await load();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    } finally {
      state =
          state.copyWith(actionLoading: {...state.actionLoading}..remove(id));
    }
  }

  Future<void> refresh() async => load();
}

final _submissionsProvider =
    StateNotifierProvider.autoDispose<_SubmissionsNotifier, _SubmissionsState>(
        (ref) {
  return _SubmissionsNotifier(ref);
});

// ── Screen ──

class SubmissionsScreen extends ConsumerWidget {
  const SubmissionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(_submissionsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Soumissions')),
      body: Column(
        children: [
          // Filter chips
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                const Icon(Icons.filter_list, size: 20),
                const SizedBox(width: 8),
                ...['submitted', 'graded', 'draft'].map((s) {
                  final selected = state.statusFilter == s;
                  return Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: FilterChip(
                      label: Text(_statusLabel(s),
                          style: const TextStyle(fontSize: 12)),
                      selected: selected,
                      onSelected: (v) => ref
                          .read(_submissionsProvider.notifier)
                          .setStatusFilter(v ? s : null),
                      visualDensity: VisualDensity.compact,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  );
                }),
              ],
            ),
          ),

          if (state.error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(state.error!,
                    style:
                        TextStyle(color: theme.colorScheme.onErrorContainer)),
              ),
            ),

          Expanded(child: _buildList(context, ref, state, theme)),
        ],
      ),
    );
  }

  Widget _buildList(BuildContext context, WidgetRef ref,
      _SubmissionsState state, ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.items.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('Aucune soumission'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(_submissionsProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length + (state.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == state.items.length) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Center(
                child: state.isLoadingMore
                    ? const CircularProgressIndicator()
                    : TextButton(
                        onPressed: () =>
                            ref.read(_submissionsProvider.notifier).loadMore(),
                        child: const Text('Charger plus'),
                      ),
              ),
            );
          }

          final sub = state.items[index];
          final isGrading = state.gradingId == sub.id;
          final isActionLoading = state.actionLoading.contains(sub.id);

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Column(
              children: [
                ListTile(
                  leading: CircleAvatar(
                    backgroundColor: _statusColor(sub.status).withAlpha(30),
                    child: Icon(Icons.description,
                        color: _statusColor(sub.status), size: 20),
                  ),
                  title: Text(sub.assignmentTitle ?? 'Devoir',
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(sub.studentName ?? sub.studentId),
                      if (sub.submittedAt != null)
                        Text(_formatDate(sub.submittedAt!),
                            style: theme.textTheme.bodySmall),
                    ],
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _SubStatusBadge(status: sub.status),
                      if (sub.score != null) ...[
                        const SizedBox(width: 8),
                        Text(
                          '${sub.score!.toStringAsFixed(1)}/${sub.assignmentTotalPoints ?? 20}',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                      ],
                    ],
                  ),
                  onTap: (sub.status == 'submitted' || sub.status == 'graded')
                      ? () => ref
                          .read(_submissionsProvider.notifier)
                          .toggleGrading(sub.id)
                      : null,
                ),
                if (isGrading)
                  _GradingForm(
                    submission: sub,
                    isLoading: isActionLoading,
                    onGrade: (score, feedback, publish) {
                      ref.read(_submissionsProvider.notifier).gradeSubmission(
                          sub.id,
                          score: score,
                          feedbackText: feedback,
                          publish: publish);
                    },
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  String _statusLabel(String s) {
    switch (s) {
      case 'submitted':
        return 'Soumis';
      case 'graded':
        return 'Noté';
      case 'draft':
        return 'Brouillon';
      default:
        return s;
    }
  }

  Color _statusColor(String s) {
    switch (s) {
      case 'submitted':
        return Colors.blue;
      case 'graded':
        return Colors.green;
      case 'draft':
        return Colors.grey;
      default:
        return Colors.grey;
    }
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat.yMMMd('fr').add_Hm().format(date);
    } catch (_) {
      return dateStr;
    }
  }
}

class _SubStatusBadge extends StatelessWidget {
  final String status;
  const _SubStatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    String label;
    switch (status) {
      case 'submitted':
        color = Colors.blue;
        label = 'Soumis';
        break;
      case 'graded':
        color = Colors.green;
        label = 'Noté';
        break;
      default:
        color = Colors.grey;
        label = 'Brouillon';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
      decoration: BoxDecoration(
        border: Border.all(color: color),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(label,
          style: TextStyle(
              fontSize: 10, color: color, fontWeight: FontWeight.w600)),
    );
  }
}

// ── Inline grading form ──

class _GradingForm extends StatefulWidget {
  final Submission submission;
  final bool isLoading;
  final void Function(double score, String? feedback, bool publish) onGrade;

  const _GradingForm({
    required this.submission,
    required this.isLoading,
    required this.onGrade,
  });

  @override
  State<_GradingForm> createState() => _GradingFormState();
}

class _GradingFormState extends State<_GradingForm> {
  late final TextEditingController _scoreController;
  late final TextEditingController _feedbackController;
  bool _publish = true;

  @override
  void initState() {
    super.initState();
    _scoreController = TextEditingController(
      text: widget.submission.score?.toStringAsFixed(1) ?? '',
    );
    _feedbackController = TextEditingController(
      text: widget.submission.feedbackText ?? '',
    );
  }

  @override
  void dispose() {
    _scoreController.dispose();
    _feedbackController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final maxPoints = widget.submission.assignmentTotalPoints ?? 20;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(12),
          bottomRight: Radius.circular(12),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Noter la soumission',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Row(
            children: [
              SizedBox(
                width: 100,
                child: TextFormField(
                  controller: _scoreController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Note',
                    suffixText: '/$maxPoints',
                    border: const OutlineInputBorder(),
                    contentPadding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _feedbackController,
                  decoration: const InputDecoration(
                    labelText: 'Commentaire',
                    border: OutlineInputBorder(),
                    contentPadding:
                        EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Checkbox(
                value: _publish,
                onChanged: (v) => setState(() => _publish = v ?? true),
              ),
              const Text('Publier immédiatement'),
              const Spacer(),
              FilledButton(
                onPressed: widget.isLoading
                    ? null
                    : () {
                        final score =
                            double.tryParse(_scoreController.text.trim());
                        if (score == null) return;
                        widget.onGrade(
                          score,
                          _feedbackController.text.trim().isNotEmpty
                              ? _feedbackController.text.trim()
                              : null,
                          _publish,
                        );
                      },
                child: widget.isLoading
                    ? const SizedBox(
                        height: 16,
                        width: 16,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : const Text('Enregistrer'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
