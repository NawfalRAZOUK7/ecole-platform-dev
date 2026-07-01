import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/domain/entities/school/micro_school.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'micro_schools_provider.dart';

class MicroSchoolDetailScreen extends ConsumerWidget {
  final String schoolId;

  const MicroSchoolDetailScreen({
    super.key,
    required this.schoolId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailAsync = ref.watch(microSchoolDetailProvider(schoolId));
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('microSchools.title')),
        actions: [
          IconButton(
            onPressed: () => context.push('/micro-schools/$schoolId/enroll'),
            icon: const Icon(Icons.person_add_alt_1),
          ),
        ],
      ),
      body: detailAsync.when(
        data: (detail) => DefaultTabController(
          length: 4,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          detail.school.name,
                          style:
                              Theme.of(context).textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.w700,
                                  ),
                        ),
                        const SizedBox(height: 8),
                        Text(detail.school.description),
                        const SizedBox(height: 12),
                        LinearProgressIndicator(
                          value: detail.school.capacityRatio.clamp(0, 1),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              TabBar(
                tabs: [
                  Tab(text: t.t('microSchools.students')),
                  Tab(text: t.t('microSchools.resources')),
                  Tab(text: t.t('microSchools.payments')),
                  Tab(text: t.t('microSchools.progress')),
                ],
              ),
              Expanded(
                child: TabBarView(
                  children: [
                    _StudentsTab(items: detail.enrollments),
                    _ResourcesTab(items: detail.resources),
                    _PaymentsTab(items: detail.payments),
                    _ProgressTab(
                      progress: detail.progress,
                      enrollments: detail.enrollments,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}

class _StudentsTab extends StatelessWidget {
  final List<MicroEnrollment> items;

  const _StudentsTab({required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const AppEmptyState(
        icon: Icons.school_outlined,
        title: 'No students enrolled',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            title: Text(item.childName),
            trailing: AppBadge(
              label: item.status,
              variant: item.status == 'active'
                  ? AppBadgeVariant.success
                  : AppBadgeVariant.neutral,
            ),
          ),
        );
      },
    );
  }
}

class _ResourcesTab extends StatelessWidget {
  final List<MicroResource> items;

  const _ResourcesTab({required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const AppEmptyState(
        icon: Icons.inventory_2_outlined,
        title: 'No resources added',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            title: Text(item.title),
            subtitle: Text(item.description),
            trailing: AppBadge(label: item.resourceType),
          ),
        );
      },
    );
  }
}

class _PaymentsTab extends StatelessWidget {
  final List<MicroPayment> items;

  const _PaymentsTab({required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const AppEmptyState(
        icon: Icons.payments_outlined,
        title: 'No payments recorded',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            title: AppCurrencyText(amount: item.amount),
            subtitle: Text(item.status),
          ),
        );
      },
    );
  }
}

class _ProgressTab extends StatelessWidget {
  final MicroProgressOverview progress;
  final List<MicroEnrollment> enrollments;

  const _ProgressTab({required this.progress, required this.enrollments});

  String _childName(String enrollmentId) {
    for (final e in enrollments) {
      if (e.id == enrollmentId) return e.childName;
    }
    return 'Enfant';
  }

  @override
  Widget build(BuildContext context) {
    final logs = progress.logs;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Observations',
                value: '${logs.length}',
                icon: Icons.photo_library_outlined,
              ),
            ),
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Active students',
                value: '${progress.activeStudents}',
                icon: Icons.groups_outlined,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        if (logs.isEmpty)
          const AppEmptyState(
            icon: Icons.timeline_outlined,
            title: 'Aucune observation pour le moment',
          )
        else
          ...logs.map(
            (log) => _ProgressFeedCard(
              log: log,
              childName: _childName(log.microEnrollmentId),
            ),
          ),
      ],
    );
  }
}

/// One entry in the Micro-École activity feed: child + date, optional photo,
/// milestone chip, and the educator's note.
class _ProgressFeedCard extends StatelessWidget {
  final MicroProgressLogEntry log;
  final String childName;

  const _ProgressFeedCard({required this.log, required this.childName});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (log.photoUrl != null && log.photoUrl!.isNotEmpty)
            ClipRRect(
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(12)),
              child: Image.network(
                log.photoUrl!,
                height: 180,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stack) => Container(
                  height: 80,
                  alignment: Alignment.center,
                  color: theme.colorScheme.surfaceContainerHighest,
                  child: Icon(
                    Icons.broken_image_outlined,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      radius: 16,
                      backgroundColor: theme.colorScheme.primaryContainer,
                      child: Text(
                        childName.isNotEmpty ? childName[0].toUpperCase() : '?',
                        style: TextStyle(
                          color: theme.colorScheme.onPrimaryContainer,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        childName,
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                    ),
                    Text(
                      log.date,
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
                if ((log.milestoneTag ?? '').isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Chip(
                    label: Text(log.milestoneTag!),
                    avatar: const Icon(Icons.emoji_events_outlined, size: 16),
                    visualDensity: VisualDensity.compact,
                    backgroundColor: theme.colorScheme.secondaryContainer,
                  ),
                ],
                if (log.note.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(log.note, style: theme.textTheme.bodyMedium),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
