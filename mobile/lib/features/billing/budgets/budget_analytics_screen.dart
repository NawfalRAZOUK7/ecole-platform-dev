import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/widgets/shimmer_skeleton.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

/// DIR oversight: budget utilization analytics for the school.
class BudgetAnalyticsScreen extends ConsumerStatefulWidget {
  const BudgetAnalyticsScreen({super.key});

  @override
  ConsumerState<BudgetAnalyticsScreen> createState() =>
      _BudgetAnalyticsScreenState();
}

class _BudgetAnalyticsScreenState
    extends ConsumerState<BudgetAnalyticsScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _data;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final res = await ref.read(apiClientProvider).get('/budgets/analytics');
      if (!mounted) return;
      setState(() => _data = res.data);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  double _num(String key) {
    final v = _data?[key];
    if (v is num) return v.toDouble();
    return double.tryParse(v?.toString() ?? '') ?? 0;
  }

  Widget _moneyCard(BuildContext context, String label, double amount) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: theme.textTheme.labelMedium),
            const SizedBox(height: 6),
            AppCurrencyText(
              amount: amount,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('budgetAnalytics.title'))),
      body: _loading
          ? const MobileListSkeleton()
          : _error != null
              ? AppErrorWidget(message: _error!, onRetry: _load)
              : _data == null || _data!.isEmpty
                  ? AppEmptyState(
                      icon: Icons.pie_chart_outline,
                      title: t.t('budgetAnalytics.empty'),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView(
                        padding: const EdgeInsets.all(16),
                        children: [
                          _moneyCard(
                            context,
                            t.t('budgetAnalytics.totalAllocated'),
                            _num('total_allocated_amount'),
                          ),
                          const SizedBox(height: 12),
                          _moneyCard(
                            context,
                            t.t('budgetAnalytics.totalSpent'),
                            _num('total_spent_amount'),
                          ),
                          const SizedBox(height: 12),
                          _moneyCard(
                            context,
                            t.t('budgetAnalytics.remaining'),
                            _num('total_remaining_unallocated'),
                          ),
                          const SizedBox(height: 12),
                          AppStatCard(
                            label: t.t('budgetAnalytics.utilization'),
                            value:
                                '${_num('utilization_rate').toStringAsFixed(1)}%',
                            icon: Icons.speed_outlined,
                          ),
                        ],
                      ),
                    ),
    );
  }
}
