import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'billing_provider.dart';

class PaymentPlanDetailScreen extends ConsumerWidget {
  final String planId;

  const PaymentPlanDetailScreen({
    super.key,
    required this.planId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final planAsync = ref.watch(paymentPlanProvider(planId));
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text('${t.t('billing.paymentPlans')} detail')),
      body: planAsync.when(
        data: (plan) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      plan.name,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(plan.studentName ?? plan.studentId),
                    const SizedBox(height: 8),
                    AppCurrencyText(
                      amount: plan.totalAmount,
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    const SizedBox(height: 8),
                    AppBadge(
                      label: plan.status,
                      variant: switch (plan.status) {
                        'completed' => AppBadgeVariant.success,
                        'cancelled' => AppBadgeVariant.error,
                        _ => AppBadgeVariant.warning,
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Installments',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 12),
            ...plan.installments.map(
              (item) => Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  leading: const Icon(Icons.schedule_outlined),
                  title: Text(_formatDate(item.dueDate)),
                  subtitle:
                      item.paidAt == null ? null : Text('Paid at ${_formatDate(item.paidAt!)}'),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      AppCurrencyText(amount: item.amount),
                      const SizedBox(height: 4),
                      AppBadge(
                        label: item.status,
                        variant: switch (item.status) {
                          'paid' => AppBadgeVariant.success,
                          'overdue' => AppBadgeVariant.error,
                          _ => AppBadgeVariant.warning,
                        },
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }

  String _formatDate(String value) {
    try {
      return DateFormat.yMMMd('fr').format(DateTime.parse(value));
    } catch (_) {
      return value;
    }
  }
}
