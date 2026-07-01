import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/widgets/shimmer_skeleton.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

/// DIR oversight: read-only view of the school's audit log entries.
class AuditLogScreen extends ConsumerStatefulWidget {
  const AuditLogScreen({super.key});

  @override
  ConsumerState<AuditLogScreen> createState() => _AuditLogScreenState();
}

class _AuditLogScreenState extends ConsumerState<AuditLogScreen> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _items = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final res = await ref
          .read(apiClientProvider)
          .list('/admin/audit-logs', params: {'limit': 50});
      if (!mounted) return;
      setState(() => _items = res.data);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _formatDate(String? iso) {
    if (iso == null) return '';
    final parsed = DateTime.tryParse(iso);
    if (parsed == null) return iso;
    return DateFormat.yMMMd().add_Hm().format(parsed.toLocal());
  }

  AppBadgeVariant _outcomeVariant(String outcome) {
    switch (outcome.toLowerCase()) {
      case 'success':
        return AppBadgeVariant.success;
      case 'failure':
      case 'error':
      case 'denied':
        return AppBadgeVariant.error;
      default:
        return AppBadgeVariant.neutral;
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('audit.title'))),
      body: _loading
          ? const MobileListSkeleton()
          : _error != null
              ? AppErrorWidget(message: _error!, onRetry: _load)
              : _items.isEmpty
                  ? AppEmptyState(
                      icon: Icons.receipt_long_outlined,
                      title: t.t('audit.empty'),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _items.length,
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          final outcome =
                              (item['outcome'] as String?) ?? '';
                          final target = [
                            item['target_type']?.toString(),
                            item['target_id']?.toString(),
                          ].whereType<String>().where((s) => s.isNotEmpty).join(' · ');
                          final subtitleParts = [
                            if (target.isNotEmpty) target,
                            _formatDate(item['created_at'] as String?),
                          ].where((s) => s.isNotEmpty);
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading:
                                  const Icon(Icons.receipt_long_outlined),
                              title: Text(
                                item['action_type']?.toString() ?? '',
                              ),
                              subtitle: Text(subtitleParts.join(' — ')),
                              trailing: outcome.isEmpty
                                  ? null
                                  : AppBadge(
                                      label: outcome,
                                      variant: _outcomeVariant(outcome),
                                    ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
