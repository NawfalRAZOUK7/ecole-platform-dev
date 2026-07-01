import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/widgets/app_snackbar.dart';
import 'package:ecole_platform/shared/ui/widgets/shimmer_skeleton.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

/// Lists the authenticated user's active sessions and allows revoking them.
class SessionsScreen extends ConsumerStatefulWidget {
  const SessionsScreen({super.key});

  @override
  ConsumerState<SessionsScreen> createState() => _SessionsScreenState();
}

class _SessionsScreenState extends ConsumerState<SessionsScreen> {
  bool _loading = true;
  String? _error;
  String? _revokingId;
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
      final res = await ref.read(apiClientProvider).list('/auth/sessions');
      if (!mounted) return;
      setState(() => _items = res.data);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _revoke(String sessionId) async {
    final t = AppLocalizations.of(ref);
    final confirmed = await AppConfirmDialog.show(
      context,
      title: t.t('sessions.revoke'),
      message: t.t('sessions.revokeConfirm'),
      confirmLabel: t.t('sessions.revoke'),
    );
    if (confirmed != true) return;

    setState(() => _revokingId = sessionId);
    try {
      await ref.read(apiClientProvider).delete('/auth/sessions/$sessionId');
      if (!mounted) return;
      AppSnackBar.show(context, t.t('sessions.revoked'));
      await _load();
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, e.toString());
    } finally {
      if (mounted) setState(() => _revokingId = null);
    }
  }

  String _formatDate(String? iso) {
    if (iso == null) return '';
    final parsed = DateTime.tryParse(iso);
    if (parsed == null) return iso;
    return DateFormat.yMMMd().add_Hm().format(parsed.toLocal());
  }

  bool _isCurrent(Map<String, dynamic> item) =>
      item['is_current'] == true || item['current'] == true;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('sessions.title'))),
      body: _loading
          ? const MobileListSkeleton()
          : _error != null
              ? AppErrorWidget(message: _error!, onRetry: _load)
              : _items.isEmpty
                  ? AppEmptyState(
                      icon: Icons.devices_outlined,
                      title: t.t('sessions.empty'),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _items.length,
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          final current = _isCurrent(item);
                          final sessionId = item['session_id']?.toString();
                          final device =
                              (item['device_name'] as String?) ??
                                  (item['source'] as String?) ??
                                  (item['user_agent'] as String?) ??
                                  '';
                          final subtitleParts = [
                            item['ip_address']?.toString(),
                            if (item['last_active'] != null)
                              '${t.t('sessions.lastActive')}: '
                                  '${_formatDate(item['last_active'] as String?)}',
                          ].whereType<String>().where((s) => s.isNotEmpty);
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: const Icon(Icons.devices_outlined),
                              title: Text(device),
                              subtitle: Text(subtitleParts.join(' · ')),
                              trailing: current
                                  ? AppBadge(
                                      label: t.t('sessions.current'),
                                      variant: AppBadgeVariant.success,
                                    )
                                  : (_revokingId == sessionId
                                      ? const SizedBox(
                                          width: 20,
                                          height: 20,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : TextButton(
                                          onPressed: sessionId == null
                                              ? null
                                              : () => _revoke(sessionId),
                                          child: Text(t.t('sessions.revoke')),
                                        )),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
