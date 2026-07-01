import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/widgets/shimmer_skeleton.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

/// Read-only view of the authenticated user's recent login history (90 days).
class LoginHistoryScreen extends ConsumerStatefulWidget {
  const LoginHistoryScreen({super.key});

  @override
  ConsumerState<LoginHistoryScreen> createState() => _LoginHistoryScreenState();
}

class _LoginHistoryScreenState extends ConsumerState<LoginHistoryScreen> {
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
          .list('/auth/login-history', params: {'limit': 50});
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

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('loginHistory.title'))),
      body: _loading
          ? const MobileListSkeleton()
          : _error != null
              ? AppErrorWidget(message: _error!, onRetry: _load)
              : _items.isEmpty
                  ? AppEmptyState(
                      icon: Icons.history,
                      title: t.t('loginHistory.empty'),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _items.length,
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          final success = item['success'] == true;
                          final device = (item['device_name'] as String?) ??
                              t.t('loginHistory.unknownDevice');
                          final location = [
                            item['city'],
                            item['country'],
                          ].whereType<String>().where((s) => s.isNotEmpty).join(', ');
                          final subtitleParts = [
                            item['ip_address']?.toString(),
                            if (location.isNotEmpty) location,
                            _formatDate(item['created_at'] as String?),
                          ].whereType<String>().where((s) => s.isNotEmpty);
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: Icon(
                                success
                                    ? Icons.check_circle_outline
                                    : Icons.error_outline,
                                color: success
                                    ? Theme.of(context).colorScheme.primary
                                    : Theme.of(context).colorScheme.error,
                              ),
                              title: Text(device),
                              subtitle: Text(subtitleParts.join(' · ')),
                              trailing: Wrap(
                                spacing: 6,
                                children: [
                                  if (item['is_new_device'] == true)
                                    AppBadge(
                                      label: t.t('loginHistory.newDevice'),
                                      variant: AppBadgeVariant.warning,
                                    ),
                                  AppBadge(
                                    label: success
                                        ? t.t('loginHistory.success')
                                        : t.t('loginHistory.failed'),
                                    variant: success
                                        ? AppBadgeVariant.success
                                        : AppBadgeVariant.error,
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
