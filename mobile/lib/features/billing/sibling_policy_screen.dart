import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'billing_provider.dart';

class SiblingPolicyScreen extends ConsumerStatefulWidget {
  const SiblingPolicyScreen({super.key});

  @override
  ConsumerState<SiblingPolicyScreen> createState() =>
      _SiblingPolicyScreenState();
}

class _SiblingPolicyScreenState extends ConsumerState<SiblingPolicyScreen> {
  bool _saving = false;

  Future<void> _editPolicy(SiblingPolicy policy) async {
    final maxController = TextEditingController(
      text: policy.maxSiblingsCovered.toString(),
    );
    final rankControllers = <TextEditingController>[];
    final discountControllers = <TextEditingController>[];
    final tiers = policy.discounts.isEmpty
        ? const [
            SiblingDiscountTier(siblingRank: 2, discountPercent: 5),
            SiblingDiscountTier(siblingRank: 3, discountPercent: 10),
          ]
        : policy.discounts;

    for (final tier in tiers) {
      rankControllers.add(
        TextEditingController(text: tier.siblingRank.toString()),
      );
      discountControllers.add(
        TextEditingController(text: tier.discountPercent.toStringAsFixed(0)),
      );
    }

    final shouldSave = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Edit sibling policy'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: maxController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Max siblings covered',
                  ),
                ),
                const SizedBox(height: 16),
                for (var index = 0;
                    index < rankControllers.length;
                    index++) ...[
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: rankControllers[index],
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            labelText: 'Sibling rank',
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextField(
                          controller: discountControllers[index],
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: const InputDecoration(
                            labelText: 'Discount %',
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
              child: Text(AppLocalizations.of(ref).t('common.save')),
            ),
          ],
        );
      },
    );

    if (shouldSave != true) {
      maxController.dispose();
      for (final controller in [...rankControllers, ...discountControllers]) {
        controller.dispose();
      }
      return;
    }

    setState(() => _saving = true);
    try {
      final discounts = <SiblingDiscountTier>[];
      for (var index = 0; index < rankControllers.length; index++) {
        discounts.add(
          SiblingDiscountTier(
            siblingRank: int.tryParse(rankControllers[index].text) ?? index + 2,
            discountPercent:
                double.tryParse(discountControllers[index].text) ?? 0,
          ),
        );
      }
      await ref.read(invoiceRepositoryProvider).updateSiblingPolicy(
            discounts: discounts,
            maxSiblingsCovered: int.tryParse(maxController.text) ?? 0,
          );
      ref.invalidate(siblingPolicyProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sibling policy updated')),
      );
    } finally {
      setState(() => _saving = false);
      maxController.dispose();
      for (final controller in [...rankControllers, ...discountControllers]) {
        controller.dispose();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final policyAsync = ref.watch(siblingPolicyProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('billing.siblingPolicy'))),
      body: policyAsync.when(
        data: (policy) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(siblingPolicyProvider),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              AppStatCard(
                label: 'Max siblings covered',
                value: '${policy.maxSiblingsCovered}',
                icon: Icons.groups_2_outlined,
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Discount tiers',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w700,
                                ),
                      ),
                      const SizedBox(height: 12),
                      if (policy.discounts.isEmpty)
                        const AppEmptyState(
                          icon: Icons.percent_outlined,
                          title: 'No sibling discounts configured',
                        )
                      else
                        ...policy.discounts.map(
                          (tier) => ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: const Icon(Icons.group_outlined),
                            title: Text('Sibling #${tier.siblingRank}'),
                            trailing: AppBadge(
                              label:
                                  '${tier.discountPercent.toStringAsFixed(0)}%',
                              variant: AppBadgeVariant.success,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _saving
            ? null
            : () {
                final current = ref.read(siblingPolicyProvider).value;
                if (current != null) {
                  _editPolicy(current);
                }
              },
        icon: _saving
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.edit_outlined),
        label: const Text('Edit'),
      ),
    );
  }
}
