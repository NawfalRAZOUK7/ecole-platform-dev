import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/compliance.dart';

final complianceAcademicYearIdProvider = Provider<String>((ref) {
  return DateTime.now().year.toString();
});

final complianceDashboardProvider =
    FutureProvider<ComplianceDashboardData>((ref) async {
  return ref.read(complianceRepositoryProvider).getDashboard(
        academicYearId: ref.read(complianceAcademicYearIdProvider),
      );
});

final complianceCurriculaProvider =
    FutureProvider<List<MenCurriculum>>((ref) async {
  return ref.read(complianceRepositoryProvider).listCurricula();
});

final complianceMappingsProvider =
    FutureProvider<List<CurriculumMapping>>((ref) async {
  return ref.read(complianceRepositoryProvider).listMappings();
});

final complianceReportsProvider =
    FutureProvider<List<ComplianceReport>>((ref) async {
  return ref.read(complianceRepositoryProvider).listReports(
    params: {
      'academic_year_id': ref.read(complianceAcademicYearIdProvider),
    },
  );
});
