import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/domain/entities/budget.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'budgets_provider.dart';

class BudgetListScreen extends ConsumerWidget {
  const BudgetListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final budgetsAsync = ref.watch(budgetsProvider);
    final analyticsAsync = ref.watch(budgetAnalyticsProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('budgets.title')),
        actions: [
          IconButton(
            onPressed: () => context.push('/budgets/requests'),
            icon: const Icon(Icons.approval_outlined),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(budgetsProvider);
          ref.invalidate(budgetAnalyticsProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            analyticsAsync.when(
              data: (analytics) => Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  SizedBox(
                    width: 160,
                    child: AppStatCard(
                      label: t.t('budgets.total'),
                      value: analytics.totalBudget.toStringAsFixed(0),
                      icon: Icons.account_balance_wallet_outlined,
                    ),
                  ),
                  SizedBox(
                    width: 160,
                    child: AppStatCard(
                      label: t.t('budgets.openRequests'),
                      value: '${analytics.openRequests}',
                      icon: Icons.receipt_long_outlined,
                    ),
                  ),
                  SizedBox(
                    width: 160,
                    child: AppStatCard(
                      label: t.t('budgets.spent'),
                      value: analytics.spentAmount.toStringAsFixed(0),
                      icon: Icons.trending_down,
                    ),
                  ),
                ],
              ),
              loading: () => const SizedBox.shrink(),
              error: (_, __) => const SizedBox.shrink(),
            ),
            const SizedBox(height: 16),
            budgetsAsync.when(
              data: (budgets) {
                if (budgets.isEmpty) {
                  return AppEmptyState(
                    icon: Icons.account_balance_wallet_outlined,
                    title: t.t('budgets.noBudgets'),
                  );
                }
                return Column(
                  children: budgets
                      .map((budget) => _BudgetCard(budget: budget, t: t))
                      .toList(),
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => AppErrorWidget(
                message: error.toString(),
                onRetry: () => ref.invalidate(budgetsProvider),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BudgetCard extends StatelessWidget {
  final BudgetEnvelope budget;
  final AppLocalizations t;

  const _BudgetCard({
    required this.budget,
    required this.t,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/budgets/${budget.id}'),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      budget.name,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  AppBadge(
                    label: budget.status,
                    variant: switch (budget.status) {
                      'active' => AppBadgeVariant.success,
                      'draft' => AppBadgeVariant.warning,
                      'closed' => AppBadgeVariant.neutral,
                      _ => AppBadgeVariant.info,
                    },
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                budget.code,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          t.t('budgets.available'),
                          style: theme.textTheme.labelMedium,
                        ),
                        AppCurrencyText(
                          amount: budget.availableAmount,
                          style: theme.textTheme.titleMedium,
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          t.t('budgets.spent'),
                          style: theme.textTheme.labelMedium,
                        ),
                        AppCurrencyText(
                          amount: budget.spentAmount,
                          style: theme.textTheme.titleMedium,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
