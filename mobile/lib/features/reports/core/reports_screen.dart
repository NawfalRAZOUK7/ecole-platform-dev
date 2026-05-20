import 'dart:async';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/reports/reporting.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/reports/core/report_schedule_manager.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

part 'reports_generator.dart';
part 'reports_history.dart';

const Map<String, List<String>> _reportTypesByRole = {
  'STD': ['student_report_card'],
  'PAR': ['student_report_card', 'billing_statement'],
  'TCH': ['class_summary', 'attendance_report'],
  'ADM': [
    'student_report_card',
    'class_summary',
    'attendance_report',
    'billing_statement',
    'school_analytics',
  ],
  'DIR': [
    'student_report_card',
    'class_summary',
    'attendance_report',
    'billing_statement',
    'school_analytics',
  ],
};

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  bool _loading = true;
  bool _loadingMore = false;
  bool _submitting = false;
  String? _error;
  ReportOptions _options = const ReportOptions();
  List<ReportJob> _jobs = [];
  List<ReportJob> _cachedReports = [];
  String? _nextCursor;
  bool _hasMore = false;
  String? _selectedType;
  String _selectedLocale = 'fr';
  String _periodId = '';
  String _classId = '';
  String _studentId = '';
  String _parentId = '';
  DateTime? _fromDate;
  DateTime? _toDate;
  bool _compare = false;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _bootstrap();
    });
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _applyState(VoidCallback update) => setState(update);

  List<String> get _availableTypes {
    final role = ref.read(authProvider).user?.role ?? 'STD';
    return _reportTypesByRole[role] ?? _reportTypesByRole['STD']!;
  }

  bool get _needsClass =>
      _selectedType == 'class_summary' || _selectedType == 'attendance_report';

  bool get _needsStudent => _selectedType == 'student_report_card';

  bool get _needsParent {
    final role = ref.read(authProvider).user?.role ?? 'STD';
    return _selectedType == 'billing_statement' && role != 'PAR';
  }

  Future<void> _bootstrap() async {
    if (!mounted) return;
    final locale = ref.read(localeProvider);
    final normalizedLocale = switch (locale) {
      'ar' => 'ar',
      'en' => 'en',
      _ => 'fr',
    };

    setState(() {
      _selectedType = _availableTypes.first;
      _selectedLocale = normalizedLocale;
    });
    await _load(refresh: true);
  }

  Future<void> _load({bool refresh = false}) async {
    if (_selectedType == null) return;

    setState(() {
      _loading = refresh || _jobs.isEmpty;
      _error = null;
    });

    try {
      final repo = ref.read(reportingRepositoryProvider);
      final results = await Future.wait([
        repo.getReportOptions(
          type: _selectedType,
          classId: _classId.isEmpty ? null : _classId,
        ),
        repo.getReportJobs(),
        repo.getCachedReports(),
      ]);

      final options = results[0] as ReportOptions;
      final history = results[1] as dynamic;
      final cachedReports = results[2] as List<ReportJob>;

      _hydrateSelections(options);
      setState(() {
        _options = options;
        _jobs = history.items as List<ReportJob>;
        _nextCursor = history.nextCursor as String?;
        _hasMore = history.hasMore as bool;
        _cachedReports = cachedReports;
        _loading = false;
      });
      _refreshPolling();
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _loadMore() async {
    if (_loadingMore || !_hasMore || _nextCursor == null) return;

    setState(() => _loadingMore = true);
    try {
      final repo = ref.read(reportingRepositoryProvider);
      final response = await repo.getReportJobs(cursor: _nextCursor);
      setState(() {
        _jobs = [..._jobs, ...response.items];
        _nextCursor = response.nextCursor;
        _hasMore = response.hasMore;
        _loadingMore = false;
      });
    } catch (e) {
      setState(() {
        _loadingMore = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _onTypeChanged(String? value) async {
    if (value == null || value == _selectedType) return;
    setState(() {
      _selectedType = value;
      _classId = '';
      _studentId = '';
      _parentId = '';
      _compare = false;
    });
    await _load(refresh: true);
  }

  Future<void> _generateReport() async {
    if (_selectedType == null) return;

    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final repo = ref.read(reportingRepositoryProvider);
      await repo.generateReport(
        type: _selectedType!,
        locale: _selectedLocale,
        periodId: _periodId,
        classId: _needsClass ? _classId : null,
        studentId: _needsStudent ? _studentId : null,
        parentId: _needsParent ? _parentId : null,
        fromDate: _periodId.isEmpty ? _formatDateParam(_fromDate) : null,
        toDate: _periodId.isEmpty ? _formatDateParam(_toDate) : null,
        compare: _selectedType == 'school_analytics' ? _compare : false,
      );
      await _load(refresh: true);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(ref).t('reports.queued'))),
        );
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  Future<void> _downloadAndOpen(ReportJob job) async {
    try {
      final file =
          await ref.read(reportingRepositoryProvider).downloadReport(job);
      await _openFile(file);
      await _load(refresh: false);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _shareReport(ReportJob job) async {
    try {
      final file =
          await ref.read(reportingRepositoryProvider).downloadReport(job);
      await Share.shareXFiles(
        [XFile(file.path)],
        text: _typeLabel(job.type, AppLocalizations.of(ref)),
      );
      await _load(refresh: false);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _openFile(File file) async {
    final result = await OpenFilex.open(file.path);
    if (result.type != ResultType.done && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${result.message} (${file.path})')),
      );
    }
  }

  void _refreshPolling() {
    _pollTimer?.cancel();
    final hasPending = _jobs.any((job) => job.isPending);
    if (!hasPending) return;
    _pollTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      _load(refresh: false);
    });
  }

  void _hydrateSelections(ReportOptions options) {
    if (_needsClass && _classId.isEmpty && options.classes.length == 1) {
      _classId = options.classes.first.id;
    }
    if (_needsStudent && _studentId.isEmpty && options.students.length == 1) {
      _studentId = options.students.first.id;
    }
    if (_needsParent && _parentId.isEmpty && options.parents.length == 1) {
      _parentId = options.parents.first.id;
    }
  }

  Future<void> _pickDate({required bool from}) async {
    final locale = ref.read(localeProvider);
    final selected = await showDatePicker(
      context: context,
      initialDate: from
          ? (_fromDate ?? DateTime.now())
          : (_toDate ?? _fromDate ?? DateTime.now()),
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
      locale: Locale(locale),
    );
    if (selected == null) return;
    setState(() {
      if (from) {
        _fromDate = selected;
        if (_toDate != null && _toDate!.isBefore(selected)) {
          _toDate = selected;
        }
      } else {
        _toDate = selected;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final textDirection =
        t.locale == 'ar' ? ui.TextDirection.rtl : ui.TextDirection.ltr;

    return Directionality(
      textDirection: textDirection,
      child: Scaffold(
        appBar: AppBar(
          title: Text(t.t('reports.title')),
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: () => _load(refresh: true),
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (_error != null) ...[
                      Card(
                        color: Theme.of(context).colorScheme.errorContainer,
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Text(
                            _error!,
                            style: TextStyle(
                              color: Theme.of(context)
                                  .colorScheme
                                  .onErrorContainer,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                    ],
                    _buildGeneratorCard(t),
                    const SizedBox(height: 16),
                    _buildHistorySection(t),
                    const SizedBox(height: 16),
                    ReportScheduleManager(
                      reportType: _selectedType ?? _availableTypes.first,
                      defaultParameters: _currentScheduleParameters(),
                    ),
                    if (_cachedReports.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      _buildCachedSection(t),
                    ],
                  ],
                ),
              ),
      ),
    );
  }
}
