import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import 'package:ecole_platform/domain/entities/child_link.dart';
import 'package:ecole_platform/features/attendance/justification_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/app_empty_state.dart';
import 'package:ecole_platform/shared/widgets/app_error_widget.dart';

class ParentJustificationScreen extends ConsumerWidget {
  const ParentJustificationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(ref);
    final async = ref.watch(justificationProvider);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('justification.title'))),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => AppErrorWidget(
          message: '$e',
          onRetry: () => ref.read(justificationProvider.notifier).refresh(),
        ),
        data: (data) {
          if (data.children.isEmpty) {
            return AppEmptyState(
              icon: Icons.family_restroom,
              title: t.t('justification.noChildren'),
            );
          }
          return RefreshIndicator(
            onRefresh: () =>
                ref.read(justificationProvider.notifier).refresh(),
            child: ListView(
              padding: const EdgeInsets.all(AppSpacing.base),
              children: <Widget>[
                Text(
                  t.t('justification.absencesHeader'),
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: AppSpacing.sm),
                for (final child in data.children)
                  _ChildAbsencesSection(
                    child: child,
                    absences: data.absencesByChild[child.userId] ??
                        const <ChildAbsence>[],
                  ),
                const SizedBox(height: AppSpacing.lg),
                Text(
                  t.t('justification.submittedHeader'),
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: AppSpacing.sm),
                if (data.submitted.isEmpty)
                  AppEmptyState(
                    icon: Icons.inbox_outlined,
                    title: t.t('justification.noSubmitted'),
                  )
                else
                  for (final j in data.submitted) _SubmittedTile(entry: j),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ChildAbsencesSection extends StatelessWidget {
  final ChildLink child;
  final List<ChildAbsence> absences;

  const _ChildAbsencesSection({required this.child, required this.absences});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final pending = absences
        .where((a) =>
            a.justificationStatus == null ||
            a.justificationStatus == 'pending')
        .toList();
    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.base),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(child.fullName,
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: AppSpacing.sm),
            if (pending.isEmpty)
              Text('—', style: theme.textTheme.bodyMedium)
            else
              for (final absence in pending)
                _AbsenceItem(child: child, absence: absence),
          ],
        ),
      ),
    );
  }
}

class _AbsenceItem extends ConsumerStatefulWidget {
  final ChildLink child;
  final ChildAbsence absence;

  const _AbsenceItem({required this.child, required this.absence});

  @override
  ConsumerState<_AbsenceItem> createState() => _AbsenceItemState();
}

class _AbsenceItemState extends ConsumerState<_AbsenceItem> {
  bool _expanded = false;
  final _reasonCtl = TextEditingController();
  File? _attachment;
  bool _submitting = false;

  @override
  void dispose() {
    _reasonCtl.dispose();
    super.dispose();
  }

  Future<void> _pickPhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked != null && mounted) {
      setState(() => _attachment = File(picked.path));
    }
  }

  Future<void> _submit() async {
    final t = AppLocalizations.of(ref);
    final reason = _reasonCtl.text.trim();
    if (reason.isEmpty) return;
    setState(() => _submitting = true);
    try {
      await ref.read(justificationProvider.notifier).submit(
            attendanceRecordId: widget.absence.recordId,
            reason: reason,
            attachment: _attachment,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(t.t('justification.submitSuccess'))),
      );
      setState(() {
        _expanded = false;
        _attachment = null;
        _reasonCtl.clear();
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$e')),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        ListTile(
          contentPadding: EdgeInsets.zero,
          title: Text(
              '${widget.absence.sessionDate} · ${widget.absence.slot}',
              style: theme.textTheme.bodyLarge),
          subtitle: widget.absence.justificationStatus == 'pending'
              ? Text(t.t('justification.alreadyPending'),
                  style: theme.textTheme.bodySmall)
              : null,
          trailing: TextButton(
            onPressed: widget.absence.justificationStatus == 'pending'
                ? null
                : () => setState(() => _expanded = !_expanded),
            child: Text(_expanded
                ? t.t('justification.cancel')
                : t.t('justification.justify')),
          ),
        ),
        if (_expanded) ...<Widget>[
          TextField(
            controller: _reasonCtl,
            maxLines: 3,
            decoration: InputDecoration(
              labelText: t.t('justification.reasonLabel'),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Row(
            children: <Widget>[
              OutlinedButton.icon(
                onPressed: _submitting ? null : _pickPhoto,
                icon: const Icon(Icons.photo),
                label: Text(_attachment == null
                    ? t.t('justification.attachPhoto')
                    : t.t('justification.photoAttached')),
              ),
              const SizedBox(width: AppSpacing.sm),
              FilledButton(
                onPressed: _submitting ? null : _submit,
                child: _submitting
                    ? const SizedBox(
                        height: 16,
                        width: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(t.t('justification.submit')),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.base),
        ],
        const Divider(height: 1),
      ],
    );
  }
}

class _SubmittedTile extends StatelessWidget {
  final SubmittedJustification entry;

  const _SubmittedTile({required this.entry});

  Color _statusColor(BuildContext context) {
    switch (entry.status) {
      case 'justified':
        return Colors.green;
      case 'rejected':
        return Theme.of(context).colorScheme.error;
      default:
        return Colors.orange;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: ListTile(
        title: Text(entry.sessionDate ?? '—'),
        subtitle: Text(
          entry.reason ?? '',
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: _statusColor(context).withAlpha(40),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            entry.status,
            style: theme.textTheme.labelSmall
                ?.copyWith(color: _statusColor(context), fontWeight: FontWeight.w700),
          ),
        ),
      ),
    );
  }
}
