/// Invoices screen — invoice list with payment status.
///
/// Reference: S-100, UI-PAR-001
/// Phase 12B: Added overdue indicators + retry payment.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/widgets/app_currency_text.dart';

import 'invoices_provider.dart';

bool _isOverdue(Invoice inv) {
  if (inv.status != 'pending') return false;
  try {
    return DateTime.parse(inv.dueDate).isBefore(DateTime.now());
  } catch (_) {
    return false;
  }
}

class InvoicesScreen extends ConsumerWidget {
  const InvoicesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(invoicesProvider);
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('invoices.title')),
        actions: [
          Semantics(
            button: true,
            label: 'Ouvrir les options de facturation',
            child: PopupMenuButton<String>(
              onSelected: context.push,
              itemBuilder: (context) => [
                PopupMenuItem(
                  value: '/billing/sibling-policy',
                  child: Text(t.t('billing.siblingPolicy')),
                ),
                PopupMenuItem(
                  value: '/billing/late-fees',
                  child: Text(t.t('billing.lateFees')),
                ),
                PopupMenuItem(
                  value: '/billing/payment-plans',
                  child: Text(t.t('billing.paymentPlans')),
                ),
              ],
            ),
          ),
        ],
      ),
      body: Semantics(
        container: true,
        label: t.t('invoices.title'),
        child: _buildBody(context, ref, state, theme, t),
      ),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, InvoicesState state,
      ThemeData theme, AppLocalizations t) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(invoicesProvider.notifier).load(),
              child: Text(t.t('common.retry')),
            ),
          ],
        ),
      );
    }

    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.receipt_long,
                size: 48, color: theme.colorScheme.outline),
            const SizedBox(height: 16),
            Text(t.t('invoices.empty')),
          ],
        ),
      );
    }

    final overdueCount = state.items.where(_isOverdue).length;

    return RefreshIndicator(
      onRefresh: () => ref.read(invoicesProvider.notifier).refresh(),
      child: Column(
        children: [
          if (overdueCount > 0)
            Semantics(
              label: '$overdueCount ${t.t('invoices.overdueLabel')}',
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                color: theme.colorScheme.errorContainer,
                child: Row(
                  children: [
                    Icon(Icons.warning_amber,
                        color: theme.colorScheme.error, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      '$overdueCount ${t.t('invoices.overdueLabel')}',
                      style: TextStyle(
                          color: theme.colorScheme.error,
                          fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
            ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: state.items.length,
              itemBuilder: (context, index) {
                final inv = state.items[index];
                final overdue = _isOverdue(inv);
                return Semantics(
                  button: true,
                  label:
                      'Facture ${inv.status}, échéance ${_formatDate(inv.dueDate)}',
                  child: Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    color: overdue ? theme.colorScheme.errorContainer : null,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(16),
                      onTap: () => context.push('/invoices/${inv.id}'),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Row(
                                  children: [
                                    _statusChip(inv.status, theme),
                                    if (overdue) ...[
                                      const SizedBox(width: 8),
                                      _overdueChip(theme, t),
                                    ],
                                  ],
                                ),
                                AppCurrencyText(
                                  amount: inv.totalAmount,
                                  currency: inv.currency,
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
                                  '${t.t('invoices.issued')}: ${_formatDate(inv.issuedDate)}',
                                  style: theme.textTheme.bodySmall,
                                ),
                                const SizedBox(width: 16),
                                const Icon(Icons.event, size: 14),
                                const SizedBox(width: 4),
                                Text(
                                  '${t.t('invoices.due')}: ${_formatDate(inv.dueDate)}',
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: overdue
                                        ? theme.colorScheme.error
                                        : null,
                                    fontWeight:
                                        overdue ? FontWeight.w600 : null,
                                  ),
                                ),
                              ],
                            ),
                            if (inv.items.isNotEmpty) ...[
                              const SizedBox(height: 12),
                              const Divider(),
                              ...inv.items.map((item) => Padding(
                                    padding:
                                        const EdgeInsets.symmetric(vertical: 4),
                                    child: Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.spaceBetween,
                                      children: [
                                        Expanded(
                                          child: Text(
                                            item.description,
                                            style: theme.textTheme.bodySmall,
                                          ),
                                        ),
                                        AppCurrencyText(
                                          amount: item.amount,
                                          currency: inv.currency,
                                          style: theme.textTheme.bodySmall
                                              ?.copyWith(
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  )),
                            ],
                            if (overdue || inv.status == 'failed') ...[
                              const SizedBox(height: 12),
                              SizedBox(
                                width: double.infinity,
                                child: Semantics(
                                  button: true,
                                  label: t.t('invoices.retry'),
                                  child: FilledButton.tonal(
                                    onPressed: state.retrying
                                        ? null
                                        : () => ref
                                            .read(invoicesProvider.notifier)
                                            .retryPayment(inv.id),
                                    child: state.retrying
                                        ? const SizedBox(
                                            width: 16,
                                            height: 16,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                            ),
                                          )
                                        : Text(t.t('invoices.retry')),
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _overdueChip(ThemeData theme, AppLocalizations t) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: theme.colorScheme.error.withAlpha(30),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: theme.colorScheme.error, width: 0.5),
      ),
      child: Text(
        t.t('invoices.overdue'),
        style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.error),
      ),
    );
  }

  Widget _statusChip(String status, ThemeData theme) {
    final (color, label) = switch (status) {
      'paid' => (theme.semanticPalette.success, 'Payée'),
      'pending' => (theme.semanticPalette.warning, 'En attente'),
      'failed' => (theme.colorScheme.error, 'Échouée'),
      'canceled' => (theme.colorScheme.outline, 'Annulée'),
      _ => (theme.colorScheme.outline, status),
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
}
