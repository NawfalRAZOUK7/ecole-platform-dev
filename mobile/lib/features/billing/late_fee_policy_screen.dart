import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'billing_provider.dart';

class LateFeePolicyScreen extends ConsumerStatefulWidget {
  const LateFeePolicyScreen({super.key});

  @override
  ConsumerState<LateFeePolicyScreen> createState() => _LateFeePolicyScreenState();
}

class _LateFeePolicyScreenState extends ConsumerState<LateFeePolicyScreen> {
  bool _saving = false;

  Future<void> _editPolicy(LateFeePolicy policy) async {
    final graceController = TextEditingController(
      text: policy.gracePeriodDays.toString(),
    );
    final percentController = TextEditingController(
      text: policy.feePercent.toStringAsFixed(1),
    );
    final capController = TextEditingController(
      text: policy.maxFeeCap.toStringAsFixed(2),
    );

    final shouldSave = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit late fee policy'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: graceController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Grace period (days)'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: percentController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Fee percent'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: capController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Max fee cap (MAD)'),
            ),
          ],
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
      ),
    );

    if (shouldSave != true) {
      graceController.dispose();
      percentController.dispose();
      capController.dispose();
      return;
    }

    setState(() => _saving = true);
    try {
      await ref.read(invoiceRepositoryProvider).updateLateFeePolicy(
            gracePeriodDays: int.tryParse(graceController.text) ?? 0,
            feePercent: double.tryParse(percentController.text) ?? 0,
            maxFeeCap: double.tryParse(capController.text) ?? 0,
          );
      ref.invalidate(lateFeePolicyProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Late fee policy updated')),
      );
    } finally {
      setState(() => _saving = false);
      graceController.dispose();
      percentController.dispose();
      capController.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final policyAsync = ref.watch(lateFeePolicyProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('billing.lateFees'))),
      body: policyAsync.when(
        data: (policy) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(lateFeePolicyProvider),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              AppStatCard(
                label: 'Grace period',
                value: '${policy.gracePeriodDays} days',
                icon: Icons.timer_outlined,
              ),
              const SizedBox(height: 12),
              AppStatCard(
                label: 'Late fee',
                value: '${policy.feePercent.toStringAsFixed(1)}%',
                icon: Icons.percent_outlined,
              ),
              const SizedBox(height: 12),
              AppStatCard(
                label: 'Maximum cap',
                value: '${policy.maxFeeCap.toStringAsFixed(2)} MAD',
                icon: Icons.money_off_csred_outlined,
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
                final current = ref.read(lateFeePolicyProvider).value;
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
