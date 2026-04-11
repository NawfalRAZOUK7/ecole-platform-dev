import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/domain/entities/budget.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'budgets_provider.dart';

class BudgetRequestScreen extends ConsumerStatefulWidget {
  const BudgetRequestScreen({super.key});

  @override
  ConsumerState<BudgetRequestScreen> createState() =>
      _BudgetRequestScreenState();
}

class _BudgetRequestScreenState extends ConsumerState<BudgetRequestScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _justificationController = TextEditingController();
  String? _selectedBudgetId;

  @override
  void dispose() {
    _amountController.dispose();
    _descriptionController.dispose();
    _justificationController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedBudgetId == null) {
      return;
    }
    await ref.read(budgetRequestActionProvider.notifier).submit(
          budgetId: _selectedBudgetId!,
          amount: double.parse(_amountController.text),
          description: _descriptionController.text.trim(),
          justification: _justificationController.text.trim(),
        );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Budget request submitted')),
    );
    _amountController.clear();
    _descriptionController.clear();
    _justificationController.clear();
  }

  @override
  Widget build(BuildContext context) {
    final budgetsAsync = ref.watch(budgetsProvider);
    final requestsAsync = ref.watch(budgetRequestsProvider);
    final actionState = ref.watch(budgetRequestActionProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('budgets.requests'))),
      body: Semantics(
        container: true,
        label: 'Demandes budgétaires',
        child: RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(budgetsProvider);
            ref.invalidate(budgetRequestsProvider);
          },
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              budgetsAsync.when(
                data: (budgets) {
                  if (_selectedBudgetId == null && budgets.isNotEmpty) {
                    _selectedBudgetId = budgets.first.id;
                  }
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          children: [
                            DropdownButtonFormField<String>(
                              initialValue: _selectedBudgetId,
                              decoration: InputDecoration(
                                labelText: t.t('budgets.envelopes'),
                                border: const OutlineInputBorder(),
                              ),
                              items: budgets
                                  .map(
                                    (budget) => DropdownMenuItem<String>(
                                      value: budget.id,
                                      child: Text(budget.name),
                                    ),
                                  )
                                  .toList(),
                              onChanged: (value) {
                                setState(() {
                                  _selectedBudgetId = value;
                                });
                              },
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _amountController,
                              keyboardType:
                                  const TextInputType.numberWithOptions(
                                decimal: true,
                              ),
                              decoration: const InputDecoration(
                                labelText: 'Amount (MAD)',
                                border: OutlineInputBorder(),
                              ),
                              validator: (value) {
                                final parsed = double.tryParse(value ?? '');
                                if (parsed == null || parsed <= 0) {
                                  return 'Enter a valid amount';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _descriptionController,
                              decoration: const InputDecoration(
                                labelText: 'Description',
                                border: OutlineInputBorder(),
                              ),
                              validator: (value) {
                                if (value == null || value.trim().isEmpty) {
                                  return 'Description is required';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _justificationController,
                              minLines: 3,
                              maxLines: 5,
                              decoration: const InputDecoration(
                                labelText: 'Justification',
                                border: OutlineInputBorder(),
                              ),
                            ),
                            const SizedBox(height: 16),
                            SizedBox(
                              width: double.infinity,
                              child: FilledButton.icon(
                                onPressed:
                                    actionState.isLoading ? null : _submit,
                                icon: actionState.isLoading
                                    ? const SizedBox(
                                        width: 16,
                                        height: 16,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                        ),
                                      )
                                    : const Icon(Icons.send_outlined),
                                label: Text(t.t('budgets.submitRequest')),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, _) => AppErrorWidget(message: error.toString()),
              ),
              const SizedBox(height: 16),
              Text(
                'Approval queue',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 12),
              requestsAsync.when(
                data: (requests) {
                  if (requests.isEmpty) {
                    return AppEmptyState(
                      icon: Icons.approval_outlined,
                      title: t.t('budgets.noRequests'),
                    );
                  }
                  return Column(
                    children: requests
                        .map(
                          (request) => _BudgetRequestCard(
                            request: request,
                            onApprove: request.status == 'pending'
                                ? () => ref
                                    .read(budgetRequestActionProvider.notifier)
                                    .approve(request.id)
                                : null,
                            onReject: request.status == 'pending'
                                ? () => ref
                                    .read(budgetRequestActionProvider.notifier)
                                    .reject(request.id)
                                : null,
                          ),
                        )
                        .toList(),
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, _) => AppErrorWidget(message: error.toString()),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BudgetRequestCard extends StatelessWidget {
  final BudgetRequest request;
  final VoidCallback? onApprove;
  final VoidCallback? onReject;

  const _BudgetRequestCard({
    required this.request,
    this.onApprove,
    this.onReject,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    request.description,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                AppBadge(
                  label: request.status,
                  variant: switch (request.status) {
                    'approved' => AppBadgeVariant.success,
                    'pending' => AppBadgeVariant.warning,
                    'rejected' => AppBadgeVariant.error,
                    _ => AppBadgeVariant.neutral,
                  },
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (request.justification != null) Text(request.justification!),
            const SizedBox(height: 12),
            Row(
              children: [
                AppCurrencyText(amount: request.amount),
                const Spacer(),
                if (onReject != null)
                  TextButton(
                    onPressed: onReject,
                    child: const Text('Reject'),
                  ),
                if (onApprove != null)
                  FilledButton.tonal(
                    onPressed: onApprove,
                    child: const Text('Approve'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
