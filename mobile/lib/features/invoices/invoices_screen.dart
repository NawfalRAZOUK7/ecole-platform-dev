/// Invoices screen — invoice list with payment status.
///
/// Reference: S-100, UI-PAR-001

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'invoices_provider.dart';

class InvoicesScreen extends ConsumerWidget {
  const InvoicesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(invoicesProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Factures')),
      body: _buildBody(context, ref, state, theme),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, InvoicesState state,
      ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(invoicesProvider.notifier).load(),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      );
    }

    if (state.items.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.receipt_long, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('Aucune facture'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(invoicesProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length,
        itemBuilder: (context, index) {
          final inv = state.items[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _statusChip(inv.status, theme),
                      Text(
                        _formatCurrency(inv.totalAmount, inv.currency),
                        style: theme.textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.calendar_today, size: 14),
                      const SizedBox(width: 4),
                      Text(
                        'Émise: ${_formatDate(inv.issuedDate)}',
                        style: theme.textTheme.bodySmall,
                      ),
                      const SizedBox(width: 16),
                      const Icon(Icons.event, size: 14),
                      const SizedBox(width: 4),
                      Text(
                        'Échéance: ${_formatDate(inv.dueDate)}',
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                  if (inv.items.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    const Divider(),
                    ...inv.items.map((item) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                  child: Text(item.description,
                                      style: theme.textTheme.bodySmall)),
                              Text(
                                _formatCurrency(item.amount, inv.currency),
                                style: theme.textTheme.bodySmall
                                    ?.copyWith(fontWeight: FontWeight.w600),
                              ),
                            ],
                          ),
                        )),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _statusChip(String status, ThemeData theme) {
    final (color, label) = switch (status) {
      'paid' => (Colors.green, 'Payée'),
      'pending' => (Colors.orange, 'En attente'),
      'failed' => (Colors.red, 'Échouée'),
      'canceled' => (Colors.grey, 'Annulée'),
      _ => (Colors.grey, status),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat.yMMMd('fr').format(date);
    } catch (_) {
      return dateStr;
    }
  }

  String _formatCurrency(double amount, String currency) {
    return NumberFormat.currency(locale: 'fr', symbol: currency).format(amount);
  }
}
