import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'skills_provider.dart';

class SkillPassportScreen extends ConsumerWidget {
  final String studentId;

  const SkillPassportScreen({
    super.key,
    required this.studentId,
  });

  Future<void> _sharePassport(WidgetRef ref) async {
    final file = await ref.read(skillsRepositoryProvider).downloadPassport(
          studentId,
          academicYearId: ref.read(academicYearIdProvider),
        );
    await Share.shareXFiles([XFile(file.path)]);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final passportAsync = ref.watch(skillPassportProvider(studentId));
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('skills.passport')),
        actions: [
          IconButton(
            onPressed: () => _sharePassport(ref),
            icon: const Icon(Icons.share_outlined),
          ),
        ],
      ),
      body: Semantics(
        container: true,
        label: t.t('skills.passport'),
        child: passportAsync.when(
          data: (passport) => ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        passport.studentName.isEmpty
                            ? studentId
                            : passport.studentName,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      const SizedBox(height: 8),
                      AppStatCard(
                        label: t.t('skills.overallScore'),
                        value: passport.overallScore.toStringAsFixed(1),
                        icon: Icons.workspace_premium_outlined,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              ...passport.dimensions.map(
                (item) => Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    title: Text(item.label),
                    trailing: Text(item.score.toStringAsFixed(1)),
                  ),
                ),
              ),
            ],
          ),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => AppErrorWidget(message: error.toString()),
        ),
      ),
    );
  }
}
