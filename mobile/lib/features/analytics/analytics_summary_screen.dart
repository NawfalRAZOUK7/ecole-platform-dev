import 'dart:ui' as ui;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/reporting.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

part 'analytics_cards.dart';
part 'analytics_charts.dart';

class AnalyticsSummaryScreen extends ConsumerStatefulWidget {
  const AnalyticsSummaryScreen({super.key});

  @override
  ConsumerState<AnalyticsSummaryScreen> createState() =>
      _AnalyticsSummaryScreenState();
}

class _AnalyticsSummaryScreenState
    extends ConsumerState<AnalyticsSummaryScreen> {
  bool _loading = true;
  String? _error;
  String _rangePreset = 'this_month';
  bool _compare = true;
  String _attendancePeriod = 'weekly';
  String _billingPeriod = 'monthly';
  String _subject = '';
  late String _fromDate;
  late String _toDate;
  AnalyticsOverview? _overview;
  AttendanceAnalytics? _attendance;
  GradesAnalytics? _grades;
  BillingAnalytics? _billing;
  EngagementAnalytics? _engagement;

  @override
  void initState() {
    super.initState();
    final range = _buildRange(_rangePreset);
    _fromDate = range.$1;
    _toDate = range.$2;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _load();
    });
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final repo = ref.read(reportingRepositoryProvider);
      final results = await Future.wait([
        repo.getOverview(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
        ),
        repo.getAttendance(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
          period: _attendancePeriod,
        ),
        repo.getGrades(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
          subject: _subject,
        ),
        repo.getBilling(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
          period: _billingPeriod,
        ),
        repo.getEngagement(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
        ),
      ]);

      setState(() {
        _overview = results[0] as AnalyticsOverview;
        _attendance = results[1] as AttendanceAnalytics;
        _grades = results[2] as GradesAnalytics;
        _billing = results[3] as BillingAnalytics;
        _engagement = results[4] as EngagementAnalytics;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  (String, String) _buildRange(String preset) {
    final now = DateTime.now();
    final today = DateFormat('yyyy-MM-dd').format(now);
    DateTime from;
    switch (preset) {
      case 'this_week':
        from = now.subtract(Duration(days: now.weekday - 1));
        break;
      case 'this_period':
        from = now.subtract(const Duration(days: 29));
        break;
      default:
        from = DateTime(now.year, now.month, 1);
        break;
    }
    return (DateFormat('yyyy-MM-dd').format(from), today);
  }

  void _applyPreset(String preset) {
    final range = _buildRange(preset);
    setState(() {
      _rangePreset = preset;
      _fromDate = range.$1;
      _toDate = range.$2;
    });
    _load();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final role = ref.watch(authProvider).user?.role ?? 'STD';
    final textDirection =
        t.locale == 'ar' ? ui.TextDirection.rtl : ui.TextDirection.ltr;

    if (role != 'ADM' && role != 'DIR') {
      return Directionality(
        textDirection: textDirection,
        child: Scaffold(
          appBar: AppBar(title: Text(t.t('analytics.title'))),
          body: Center(child: Text(t.t('analytics.restricted'))),
        ),
      );
    }

    return Directionality(
      textDirection: textDirection,
      child: Scaffold(
        appBar: AppBar(
          title: Text(t.t('analytics.title')),
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _load,
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
                    _buildToolbar(t),
                    const SizedBox(height: 16),
                    _buildKpis(t),
                    const SizedBox(height: 16),
                    _buildAttendanceCard(t),
                    const SizedBox(height: 16),
                    _buildGradesCard(t),
                    const SizedBox(height: 16),
                    _buildBillingCard(t),
                    const SizedBox(height: 16),
                    _buildEngagementCard(t),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildToolbar(AppLocalizations t) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${_fromDate} → $_toDate',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _PresetChip(
                  label: t.t('analytics.presets.this_week'),
                  selected: _rangePreset == 'this_week',
                  onTap: () => _applyPreset('this_week'),
                ),
                _PresetChip(
                  label: t.t('analytics.presets.this_month'),
                  selected: _rangePreset == 'this_month',
                  onTap: () => _applyPreset('this_month'),
                ),
                _PresetChip(
                  label: t.t('analytics.presets.this_period'),
                  selected: _rangePreset == 'this_period',
                  onTap: () => _applyPreset('this_period'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _compare,
              title: Text(t.t('analytics.compare')),
              onChanged: (value) {
                setState(() => _compare = value);
                _load();
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKpis(AppLocalizations t) {
    final metrics = _overview?.metrics ?? const {};
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        _MetricCard(
          title: t.t('analytics.kpis.activeUsers'),
          metric: metrics['active_users'] ?? const AnalyticsMetric(current: 0),
          suffix: '',
          onTap: () => _showDetailSheet(
            title: t.t('analytics.kpis.activeUsers'),
            child: _FunnelChartCard(funnel: _engagement?.funnel ?? const []),
          ),
        ),
        _MetricCard(
          title: t.t('analytics.kpis.attendanceRate'),
          metric:
              metrics['attendance_rate'] ?? const AnalyticsMetric(current: 0),
          suffix: '%',
          onTap: () => _showDetailSheet(
            title: t.t('analytics.kpis.attendanceRate'),
            child: _AttendanceChart(series: _attendance?.series ?? const []),
          ),
        ),
        _MetricCard(
          title: t.t('analytics.kpis.averageGrade'),
          metric: metrics['average_grade'] ?? const AnalyticsMetric(current: 0),
          suffix: '',
          onTap: () => _showDetailSheet(
            title: t.t('analytics.kpis.averageGrade'),
            child: _DistributionChart(
              buckets: _grades?.distribution ?? const [],
              color: Theme.of(context).semanticPalette.success,
            ),
          ),
        ),
        _MetricCard(
          title: t.t('analytics.kpis.collectionRate'),
          metric:
              metrics['collection_rate'] ?? const AnalyticsMetric(current: 0),
          suffix: '%',
          onTap: () => _showDetailSheet(
            title: t.t('analytics.kpis.collectionRate'),
            child: _WaterfallChart(
              values: [
                _billing?.invoiced ?? 0,
                _billing?.paid ?? 0,
                _billing?.outstanding ?? 0,
              ],
              labels: [
                t.t('analytics.stages.invoiced'),
                t.t('analytics.stages.paid'),
                t.t('analytics.stages.outstanding'),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildAttendanceCard(AppLocalizations t) {
    return _SectionCard(
      title: t.t('analytics.charts.attendance'),
      subtitle: t.t('analytics.buckets.$_attendancePeriod'),
      action: DropdownButton<String>(
        value: _attendancePeriod,
        underline: const SizedBox.shrink(),
        items: ['daily', 'weekly', 'monthly']
            .map(
              (item) => DropdownMenuItem(
                value: item,
                child: Text(t.t('analytics.buckets.$item')),
              ),
            )
            .toList(),
        onChanged: (value) {
          if (value == null) return;
          setState(() => _attendancePeriod = value);
          _load();
        },
      ),
      child: _AttendanceChart(series: _attendance?.series ?? const []),
    );
  }

  Widget _buildGradesCard(AppLocalizations t) {
    return _SectionCard(
      title: t.t('analytics.charts.grades'),
      subtitle: t.t('analytics.subjectHint'),
      action: SizedBox(
        width: 140,
        child: TextField(
          controller: TextEditingController(text: _subject),
          decoration: InputDecoration(
            hintText: t.t('analytics.subjectPlaceholder'),
            isDense: true,
          ),
          onSubmitted: (value) {
            setState(() => _subject = value);
            _load();
          },
        ),
      ),
      child: _DistributionChart(
        buckets: _grades?.distribution ?? const [],
        color: Theme.of(context).semanticPalette.success,
      ),
    );
  }

  Widget _buildBillingCard(AppLocalizations t) {
    return _SectionCard(
      title: t.t('analytics.charts.billing'),
      subtitle: t.t('analytics.buckets.$_billingPeriod'),
      action: DropdownButton<String>(
        value: _billingPeriod,
        underline: const SizedBox.shrink(),
        items: ['daily', 'weekly', 'monthly']
            .map(
              (item) => DropdownMenuItem(
                value: item,
                child: Text(t.t('analytics.buckets.$item')),
              ),
            )
            .toList(),
        onChanged: (value) {
          if (value == null) return;
          setState(() => _billingPeriod = value);
          _load();
        },
      ),
      child: _WaterfallChart(
        values: [
          _billing?.invoiced ?? 0,
          _billing?.paid ?? 0,
          _billing?.outstanding ?? 0,
        ],
        labels: [
          t.t('analytics.stages.invoiced'),
          t.t('analytics.stages.paid'),
          t.t('analytics.stages.outstanding'),
        ],
      ),
    );
  }

  Widget _buildEngagementCard(AppLocalizations t) {
    return _SectionCard(
      title: t.t('analytics.charts.engagement'),
      subtitle: t.t('analytics.charts.engagementHint'),
      child: _FunnelChartCard(funnel: _engagement?.funnel ?? const []),
    );
  }

  void _showDetailSheet({
    required String title,
    required Widget child,
  }) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 16),
                SizedBox(height: 260, child: child),
              ],
            ),
          ),
        );
      },
    );
  }
}
