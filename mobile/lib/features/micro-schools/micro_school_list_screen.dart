import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/domain/entities/micro_school.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'micro_schools_provider.dart';

class MicroSchoolListScreen extends ConsumerWidget {
  const MicroSchoolListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final schoolsAsync = ref.watch(microSchoolsProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('microSchools.title'))),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(microSchoolsProvider),
        child: schoolsAsync.when(
          data: (schools) {
            if (schools.isEmpty) {
              return AppEmptyState(
                icon: Icons.location_city_outlined,
                title: t.t('microSchools.noSchools'),
              );
            }
            return GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 0.9,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: schools.length,
              itemBuilder: (context, index) => _SchoolCard(
                school: schools[index],
                t: t,
              ),
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => AppErrorWidget(message: error.toString()),
        ),
      ),
    );
  }
}

class _SchoolCard extends StatelessWidget {
  final MicroSchool school;
  final AppLocalizations t;

  const _SchoolCard({
    required this.school,
    required this.t,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/micro-schools/${school.id}'),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      school.name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                  ),
                  AppBadge(
                    label: school.status,
                    variant: school.status == 'active'
                        ? AppBadgeVariant.success
                        : AppBadgeVariant.neutral,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                school.city,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const Spacer(),
              Text(
                '${t.t('microSchools.capacity')} ${school.studentCount}/${school.capacity}',
              ),
              const SizedBox(height: 8),
              LinearProgressIndicator(value: school.capacityRatio.clamp(0, 1)),
            ],
          ),
        ),
      ),
    );
  }
}
