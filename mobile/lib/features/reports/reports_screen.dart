import 'dart:async';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/reporting.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

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
                        color: Colors.red.shade50,
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Text(
                            _error!,
                            style: const TextStyle(color: Colors.red),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                    ],
                    _buildGeneratorCard(t),
                    const SizedBox(height: 16),
                    _buildHistorySection(t),
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

  Widget _buildGeneratorCard(AppLocalizations t) {
    final role = ref.watch(authProvider).user?.role ?? 'STD';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    t.t('reports.generateTitle'),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Chip(label: Text(role)),
              ],
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _selectedType,
              decoration:
                  InputDecoration(labelText: t.t('reports.fields.type')),
              items: _availableTypes
                  .map(
                    (item) => DropdownMenuItem(
                      value: item,
                      child: Text(_typeLabel(item, t)),
                    ),
                  )
                  .toList(),
              onChanged: _onTypeChanged,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _selectedLocale,
              decoration:
                  InputDecoration(labelText: t.t('reports.fields.language')),
              items: const [
                DropdownMenuItem(value: 'fr', child: Text('Français')),
                DropdownMenuItem(value: 'ar', child: Text('العربية')),
                DropdownMenuItem(value: 'en', child: Text('English')),
              ],
              onChanged: (value) {
                if (value != null) {
                  setState(() => _selectedLocale = value);
                }
              },
            ),
            if (_options.periods.isNotEmpty) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _periodId.isEmpty ? null : _periodId,
                decoration:
                    InputDecoration(labelText: t.t('reports.fields.period')),
                items: [
                  DropdownMenuItem(
                    value: '',
                    child: Text(t.t('reports.anyPeriod')),
                  ),
                  ..._options.periods.map(
                    (period) => DropdownMenuItem(
                      value: period.id,
                      child: Text(period.label),
                    ),
                  ),
                ],
                onChanged: (value) {
                  setState(() {
                    _periodId = value ?? '';
                  });
                },
              ),
            ],
            if (_needsClass) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _classId.isEmpty ? null : _classId,
                decoration:
                    InputDecoration(labelText: t.t('reports.fields.class')),
                items: _options.classes
                    .map(
                      (item) => DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          item.secondary == null
                              ? item.label
                              : '${item.label} · ${item.secondary}',
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  setState(() => _classId = value ?? '');
                  _load(refresh: false);
                },
              ),
            ],
            if (_needsStudent && _options.students.isNotEmpty) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _studentId.isEmpty ? null : _studentId,
                decoration:
                    InputDecoration(labelText: t.t('reports.fields.student')),
                items: _options.students
                    .map(
                      (item) => DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          item.secondary == null
                              ? item.label
                              : '${item.label} · ${item.secondary}',
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  setState(() => _studentId = value ?? '');
                },
              ),
            ],
            if (_needsParent && _options.parents.isNotEmpty) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _parentId.isEmpty ? null : _parentId,
                decoration:
                    InputDecoration(labelText: t.t('reports.fields.parent')),
                items: _options.parents
                    .map(
                      (item) => DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          item.secondary == null
                              ? item.label
                              : '${item.label} · ${item.secondary}',
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  setState(() => _parentId = value ?? '');
                },
              ),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _DateTile(
                    label: t.t('reports.fields.from'),
                    value: _displayDate(_fromDate, t.locale),
                    onTap:
                        _periodId.isEmpty ? () => _pickDate(from: true) : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _DateTile(
                    label: t.t('reports.fields.to'),
                    value: _displayDate(_toDate, t.locale),
                    onTap:
                        _periodId.isEmpty ? () => _pickDate(from: false) : null,
                  ),
                ),
              ],
            ),
            if (_selectedType == 'school_analytics') ...[
              const SizedBox(height: 12),
              SwitchListTile(
                value: _compare,
                contentPadding: EdgeInsets.zero,
                title: Text(t.t('reports.comparePrevious')),
                onChanged: (value) {
                  setState(() => _compare = value);
                },
              ),
            ],
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _submitting ? null : _generateReport,
                icon: _submitting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.picture_as_pdf_outlined),
                label: Text(
                  _submitting
                      ? t.t('reports.generating')
                      : t.t('reports.generate'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistorySection(AppLocalizations t) {
    final pendingCount = _jobs.where((item) => item.isPending).length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                t.t('reports.historyTitle'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            if (pendingCount > 0)
              Chip(
                avatar: const Icon(Icons.schedule, size: 16),
                label: Text('$pendingCount ${t.t('reports.pending')}'),
              ),
          ],
        ),
        const SizedBox(height: 12),
        if (_jobs.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(t.t('reports.empty')),
            ),
          )
        else
          ..._jobs.map((job) => _buildHistoryCard(job, t)),
        if (_hasMore) ...[
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: _loadingMore ? null : _loadMore,
            child: _loadingMore
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(t.t('reports.loadMore')),
          ),
        ],
      ],
    );
  }

  Widget _buildCachedSection(AppLocalizations t) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t.t('reports.cachedTitle'),
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        ..._cachedReports.map((job) => _buildHistoryCard(job, t, cached: true)),
      ],
    );
  }

  Widget _buildHistoryCard(
    ReportJob job,
    AppLocalizations t, {
    bool cached = false,
  }) {
    final fileExists =
        job.localFilePath != null && File(job.localFilePath!).existsSync();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _typeLabel(job.type, t),
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _describeScope(job, t),
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                _StatusChip(
                  label: _statusLabel(job.status, t),
                  status: job.status,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.schedule, size: 14),
                const SizedBox(width: 6),
                Text(
                  _formatDateTime(job.createdAt, t.locale),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
            if (cached || fileExists) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.offline_pin_outlined, size: 14),
                  const SizedBox(width: 6),
                  Text(
                    t.t('reports.availableOffline'),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ],
            if (job.errorMessage != null && job.errorMessage!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                job.errorMessage!,
                style: const TextStyle(color: Colors.red),
              ),
            ],
            if (job.isReady || fileExists) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilledButton.tonalIcon(
                    onPressed: () => _downloadAndOpen(job),
                    icon: const Icon(Icons.open_in_new),
                    label: Text(t.t('reports.open')),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _shareReport(job),
                    icon: const Icon(Icons.share_outlined),
                    label: Text(t.t('reports.share')),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _typeLabel(String type, AppLocalizations t) {
    return t.t('reports.types.$type');
  }

  String _statusLabel(String status, AppLocalizations t) {
    return t.t('reports.status.$status');
  }

  String _describeScope(ReportJob job, AppLocalizations t) {
    final parameters = job.parameters;
    if (parameters['period_label'] != null) {
      return parameters['period_label'].toString();
    }
    if (parameters['from_date'] != null && parameters['to_date'] != null) {
      return '${parameters['from_date']} → ${parameters['to_date']}';
    }
    if (parameters['student_id'] != null) {
      return '${t.t('reports.fields.student')}: ${parameters['student_id']}';
    }
    if (parameters['class_id'] != null) {
      return '${t.t('reports.fields.class')}: ${parameters['class_id']}';
    }
    if (parameters['parent_id'] != null) {
      return '${t.t('reports.fields.parent')}: ${parameters['parent_id']}';
    }
    return t.t('reports.scopeDefault');
  }

  String _displayDate(DateTime? value, String locale) {
    if (value == null) return '—';
    return DateFormat.yMMMd(locale).format(value);
  }

  String _formatDateTime(String value, String locale) {
    try {
      return DateFormat.yMMMd(locale)
          .add_Hm()
          .format(DateTime.parse(value).toLocal());
    } catch (_) {
      return value;
    }
  }

  String? _formatDateParam(DateTime? value) {
    if (value == null) return null;
    return DateFormat('yyyy-MM-dd').format(value);
  }
}

class _DateTile extends StatelessWidget {
  final String label;
  final String value;
  final VoidCallback? onTap;

  const _DateTile({
    required this.label,
    required this.value,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          enabled: onTap != null,
        ),
        child: Row(
          children: [
            Expanded(child: Text(value)),
            const Icon(Icons.calendar_today_outlined, size: 18),
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String label;
  final String status;

  const _StatusChip({
    required this.label,
    required this.status,
  });

  @override
  Widget build(BuildContext context) {
    final (color, background) = switch (status) {
      'ready' => (Colors.green.shade800, Colors.green.shade50),
      'failed' => (Colors.red.shade800, Colors.red.shade50),
      'generating' => (Colors.orange.shade800, Colors.orange.shade50),
      _ => (Colors.blue.shade800, Colors.blue.shade50),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
      ),
    );
  }
}
