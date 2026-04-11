import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'billing_provider.dart';

class PaymentPlansScreen extends ConsumerStatefulWidget {
  const PaymentPlansScreen({super.key});

  @override
  ConsumerState<PaymentPlansScreen> createState() => _PaymentPlansScreenState();
}

class _PaymentPlansScreenState extends ConsumerState<PaymentPlansScreen> {
  bool _creating = false;

  Future<void> _createPlan() async {
    final studentController = TextEditingController();
    final nameController = TextEditingController();
    final totalController = TextEditingController();
    final startController = TextEditingController(
      text: DateFormat('yyyy-MM-dd').format(DateTime.now()),
    );
    final dueControllers = List.generate(
      3,
      (index) => TextEditingController(
        text: DateFormat('yyyy-MM-dd').format(
          DateTime.now().add(Duration(days: 30 * (index + 1))),
        ),
      ),
    );
    final amountControllers = List.generate(
      3,
      (_) => TextEditingController(text: '0'),
    );

    final shouldCreate = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create payment plan'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: studentController,
                decoration: const InputDecoration(labelText: 'Student ID'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Plan name'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: totalController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration:
                    const InputDecoration(labelText: 'Total amount (MAD)'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: startController,
                decoration: const InputDecoration(labelText: 'Start date'),
              ),
              const SizedBox(height: 16),
              for (var index = 0; index < dueControllers.length; index++) ...[
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: dueControllers[index],
                        decoration: InputDecoration(
                          labelText: 'Due date ${index + 1}',
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: amountControllers[index],
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        decoration: InputDecoration(
                          labelText: 'Amount ${index + 1}',
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(AppLocalizations.of(ref).t('common.cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Create'),
          ),
        ],
      ),
    );

    if (shouldCreate != true) {
      for (final controller in [
        studentController,
        nameController,
        totalController,
        startController,
        ...dueControllers,
        ...amountControllers,
      ]) {
        controller.dispose();
      }
      return;
    }

    setState(() => _creating = true);
    try {
      await ref.read(invoiceRepositoryProvider).createPaymentPlan(
            studentId: studentController.text.trim(),
            name: nameController.text.trim(),
            totalAmount: double.tryParse(totalController.text) ?? 0,
            startDate: startController.text.trim(),
            installments: List.generate(
              dueControllers.length,
              (index) => PaymentPlanDraftInstallment(
                dueDate: dueControllers[index].text.trim(),
                amount: double.tryParse(amountControllers[index].text) ?? 0,
              ),
            ),
          );
      ref.invalidate(paymentPlansProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Payment plan created')),
      );
    } finally {
      setState(() => _creating = false);
      for (final controller in [
        studentController,
        nameController,
        totalController,
        startController,
        ...dueControllers,
        ...amountControllers,
      ]) {
        controller.dispose();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final plansAsync = ref.watch(paymentPlansProvider);
    final status = ref.watch(billingStatusFilterProvider);
    final t = AppLocalizations.of(ref);
    const filters = [
      (null, 'All'),
      ('active', 'Active'),
      ('completed', 'Completed'),
      ('cancelled', 'Cancelled'),
    ];

    return Scaffold(
      appBar: AppBar(title: Text(t.t('billing.paymentPlans'))),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Row(
              children: filters
                  .map(
                    (filter) => Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(filter.$2),
                        selected: status == filter.$1,
                        onSelected: (_) {
                          ref.read(billingStatusFilterProvider.notifier).state =
                              filter.$1;
                        },
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
          Expanded(
            child: plansAsync.when(
              data: (plans) {
                if (plans.isEmpty) {
                  return const AppEmptyState(
                    icon: Icons.event_note_outlined,
                    title: 'No payment plans configured',
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async => ref.invalidate(paymentPlansProvider),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: plans.length,
                    itemBuilder: (context, index) {
                      final plan = plans[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          onTap: () =>
                              context.push('/billing/payment-plans/${plan.id}'),
                          leading: const Icon(Icons.event_note_outlined),
                          title: Text(plan.name),
                          subtitle: Text(
                            '${plan.studentName ?? plan.studentId} · ${plan.installments.length} installments',
                          ),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              AppCurrencyText(amount: plan.totalAmount),
                              const SizedBox(height: 4),
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
                      );
                    },
                  ),
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => AppErrorWidget(message: error.toString()),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _creating ? null : _createPlan,
        icon: _creating
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.add_outlined),
        label: const Text('Create plan'),
      ),
    );
  }
}
