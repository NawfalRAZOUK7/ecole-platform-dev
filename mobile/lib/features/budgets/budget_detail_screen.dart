import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/domain/entities/budget.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'budgets_provider.dart';

class BudgetDetailScreen extends ConsumerWidget {
  final String budgetId;

  const BudgetDetailScreen({
    super.key,
    required this.budgetId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailAsync = ref.watch(budgetDetailProvider(budgetId));
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('budgets.detail'))),
      body: Semantics(
        container: true,
        label: 'Détail du budget',
        child: detailAsync.when(
          data: (detail) => DefaultTabController(
            length: 3,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: _BudgetOverview(detail: detail, t: t),
                ),
                TabBar(
                  tabs: [
                    Tab(text: t.t('budgets.allocations')),
                    Tab(text: t.t('budgets.transactions')),
                    Tab(text: t.t('budgets.requests')),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      _AllocationsTab(items: detail.allocations),
                      _TransactionsTab(items: detail.transactions),
                      _RequestsTab(items: detail.requests),
                    ],
                  ),
                ),
              ],
            ),
          ),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => AppErrorWidget(message: error.toString()),
        ),
      ),
    );
  }
}

class _BudgetOverview extends StatelessWidget {
  final BudgetDetailBundle detail;
  final AppLocalizations t;

  const _BudgetOverview({
    required this.detail,
    required this.t,
  });

  @override
  Widget build(BuildContext context) {
    final sections = [
      PieChartSectionData(
        value: detail.analytics.allocatedAmount,
        color: Theme.of(context).colorScheme.primary,
        title: 'Alloc.',
      ),
      PieChartSectionData(
        value: detail.analytics.spentAmount,
        color: Theme.of(context).colorScheme.error,
        title: 'Spent',
      ),
      PieChartSectionData(
        value: detail.analytics.availableAmount,
        color: Theme.of(context).colorScheme.tertiary,
        title: 'Avail.',
      ),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              detail.budget.name,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 200,
              child: Row(
                children: [
                  Expanded(
                    child: PieChart(
                      PieChartData(
                        sectionsSpace: 2,
                        centerSpaceRadius: 36,
                        sections: sections,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          t.t('budgets.total'),
                          style: Theme.of(context).textTheme.labelLarge,
                        ),
                        AppCurrencyText(
                          amount: detail.budget.totalAmount,
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          t.t('budgets.available'),
                          style: Theme.of(context).textTheme.labelLarge,
                        ),
                        AppCurrencyText(
                          amount: detail.analytics.availableAmount,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AllocationsTab extends StatelessWidget {
  final List<BudgetAllocation> items;

  const _AllocationsTab({required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const AppEmptyState(
        icon: Icons.pie_chart_outline,
        title: 'No allocations yet',
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
            title: Text(item.label),
            subtitle: Text(
              'Committed ${item.committedAmount.toStringAsFixed(0)} • Spent ${item.spentAmount.toStringAsFixed(0)}',
            ),
            trailing: AppCurrencyText(amount: item.amount),
          ),
        );
      },
    );
  }
}

class _TransactionsTab extends StatelessWidget {
  final List<BudgetTransaction> items;

  const _TransactionsTab({required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const AppEmptyState(
        icon: Icons.swap_horiz,
        title: 'No transactions available',
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
            title: Text(item.description),
            subtitle: Text(item.direction),
            trailing: AppCurrencyText(amount: item.amount),
          ),
        );
      },
    );
  }
}

class _RequestsTab extends StatelessWidget {
  final List<BudgetRequest> items;

  const _RequestsTab({required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const AppEmptyState(
        icon: Icons.approval_outlined,
        title: 'No requests recorded',
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
            title: Text(item.description),
            subtitle: Text(item.justification ?? item.status),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                AppCurrencyText(amount: item.amount),
                const SizedBox(height: 4),
                AppBadge(
                  label: item.status,
                  variant: switch (item.status) {
                    'approved' => AppBadgeVariant.success,
                    'pending' => AppBadgeVariant.warning,
                    'rejected' => AppBadgeVariant.error,
                    _ => AppBadgeVariant.neutral,
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
