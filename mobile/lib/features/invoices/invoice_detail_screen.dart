import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'invoices_provider.dart';

class InvoiceDetailScreen extends ConsumerStatefulWidget {
  final String invoiceId;

  const InvoiceDetailScreen({
    super.key,
    required this.invoiceId,
  });

  @override
  ConsumerState<InvoiceDetailScreen> createState() =>
      _InvoiceDetailScreenState();
}

class _InvoiceDetailScreenState extends ConsumerState<InvoiceDetailScreen> {
  bool _submittingPayment = false;
  bool _uploadingProof = false;
  bool _downloadingPdf = false;
  bool _downloadingReceipt = false;

  Future<void> _createPayment(Invoice invoice) async {
    final amountController = TextEditingController(
      text: (invoice.balanceDue ?? invoice.totalAmount).toStringAsFixed(2),
    );
    String method = 'card';
    final created = await showDialog<bool>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: const Text('Create payment'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: amountController,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    decoration: const InputDecoration(labelText: 'Amount'),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: method,
                    items: const [
                      DropdownMenuItem(value: 'card', child: Text('Card')),
                      DropdownMenuItem(value: 'cash', child: Text('Cash')),
                      DropdownMenuItem(
                        value: 'transfer',
                        child: Text('Transfer'),
                      ),
                    ],
                    onChanged: (value) {
                      if (value == null) return;
                      setStateDialog(() {
                        method = value;
                      });
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(false),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () => Navigator.of(context).pop(true),
                  child: const Text('Create'),
                ),
              ],
            );
          },
        );
      },
    );

    if (created != true) return;

    setState(() => _submittingPayment = true);
    try {
      final amount =
          double.tryParse(amountController.text) ?? invoice.totalAmount;
      await ref.read(invoiceRepositoryProvider).createPayment(
            invoiceId: widget.invoiceId,
            amount: amount,
            method: method,
          );
      ref.invalidate(invoiceDetailProvider(widget.invoiceId));
      ref.read(invoicesProvider.notifier).refresh();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Payment created')),
      );
    } finally {
      if (mounted) {
        setState(() => _submittingPayment = false);
      }
      amountController.dispose();
    }
  }

  Future<void> _uploadProof(String paymentId) async {
    final result = await FilePicker.platform.pickFiles();
    final path = result?.files.single.path;
    if (path == null) return;

    setState(() => _uploadingProof = true);
    try {
      await ref.read(invoiceRepositoryProvider).uploadPaymentProof(
            paymentId: paymentId,
            file: File(path),
          );
      ref.invalidate(invoiceDetailProvider(widget.invoiceId));
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Payment proof uploaded')),
      );
    } finally {
      if (mounted) {
        setState(() => _uploadingProof = false);
      }
    }
  }

  Future<String?> _showLanguageDialog(String title) async {
    String language = 'fr';
    return showDialog<String>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setStateDialog) => AlertDialog(
          title: Text(title),
          content: DropdownButtonFormField<String>(
            initialValue: language,
            items: const [
              DropdownMenuItem(value: 'fr', child: Text('Français')),
              DropdownMenuItem(value: 'ar', child: Text('العربية')),
            ],
            onChanged: (v) => setStateDialog(() => language = v ?? 'fr'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, language),
              child: const Text('Download'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _downloadPdf() async {
    final language = await _showLanguageDialog('PDF Language');
    if (language == null || !mounted) return;

    setState(() => _downloadingPdf = true);
    try {
      final file = await ref.read(invoiceRepositoryProvider).downloadInvoicePdf(
            widget.invoiceId,
            language: language,
          );
      await OpenFilex.open(file.path);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('PDF downloaded: ${file.path.split('/').last}')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      if (mounted) setState(() => _downloadingPdf = false);
    }
  }

  Future<void> _downloadReceipt(String paymentId) async {
    final language = await _showLanguageDialog('Receipt Language');
    if (language == null || !mounted) return;

    setState(() => _downloadingReceipt = true);
    try {
      final file = await ref
          .read(invoiceRepositoryProvider)
          .downloadPaymentReceipt(paymentId, language: language);
      await OpenFilex.open(file.path);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Receipt downloaded: ${file.path.split('/').last}'),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      if (mounted) setState(() => _downloadingReceipt = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(invoiceDetailProvider(widget.invoiceId));
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('invoices.detail')),
        actions: [
          IconButton(
            onPressed: _downloadingPdf ? null : _downloadPdf,
            icon: _downloadingPdf
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.picture_as_pdf_outlined),
          ),
        ],
      ),
      body: detailAsync.when(
        data: (detail) => RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(invoiceDetailProvider(widget.invoiceId));
          },
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        detail.invoice.label ??
                            detail.invoice.invoiceNumber ??
                            detail.invoice.id,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      const SizedBox(height: 8),
                      AppCurrencyText(
                        amount: detail.invoice.totalAmount,
                        currency: detail.invoice.currency,
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      if (detail.invoice.balanceDue != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          '${t.t('invoices.balanceDue')}: ${detail.invoice.balanceDue!.toStringAsFixed(2)} ${detail.invoice.currency}',
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                t.t('invoices.lineItems'),
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 12),
              ...detail.invoice.items.map(
                (item) => Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    title: Text(item.description),
                    subtitle: Text(
                      '${item.quantity} × ${item.unitPrice.toStringAsFixed(2)} ${detail.invoice.currency}',
                    ),
                    trailing: AppCurrencyText(
                      amount: item.amount,
                      currency: detail.invoice.currency,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      t.t('invoices.paymentHistory'),
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                  ),
                  FilledButton.tonalIcon(
                    onPressed: _submittingPayment
                        ? null
                        : () => _createPayment(detail.invoice),
                    icon: _submittingPayment
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.add_card_outlined),
                    label: Text(t.t('invoices.createPayment')),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (detail.payments.isEmpty)
                AppEmptyState(
                  icon: Icons.payments_outlined,
                  title: t.t('invoices.noPayments'),
                )
              else
                ...detail.payments.map(
                  (payment) => _PaymentCard(
                    payment: payment,
                    uploading: _uploadingProof,
                    downloadingReceipt: _downloadingReceipt,
                    onUploadProof: () => _uploadProof(payment.id),
                    onDownloadReceipt: () => _downloadReceipt(payment.id),
                  ),
                ),
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}

class _PaymentCard extends StatelessWidget {
  final InvoicePaymentRecord payment;
  final bool uploading;
  final bool downloadingReceipt;
  final VoidCallback onUploadProof;
  final VoidCallback onDownloadReceipt;

  const _PaymentCard({
    required this.payment,
    required this.uploading,
    required this.downloadingReceipt,
    required this.onUploadProof,
    required this.onDownloadReceipt,
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
                    payment.method.toUpperCase(),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                AppBadge(
                  label: payment.status,
                  variant: switch (payment.status) {
                    'succeeded' => AppBadgeVariant.success,
                    'completed' => AppBadgeVariant.success,
                    'failed' => AppBadgeVariant.error,
                    'pending' => AppBadgeVariant.warning,
                    _ => AppBadgeVariant.neutral,
                  },
                ),
              ],
            ),
            const SizedBox(height: 8),
            AppCurrencyText(amount: payment.amount),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                FilledButton.tonalIcon(
                  onPressed: downloadingReceipt ? null : onDownloadReceipt,
                  icon: downloadingReceipt
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.receipt_long_outlined),
                  label: const Text('Receipt'),
                ),
                const SizedBox(width: 8),
                FilledButton.tonalIcon(
                  onPressed: uploading ? null : onUploadProof,
                  icon: uploading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.upload_file_outlined),
                  label: const Text('Upload proof'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
