import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

class GdprScreen extends ConsumerStatefulWidget {
  const GdprScreen({super.key});

  @override
  ConsumerState<GdprScreen> createState() => _GdprScreenState();
}

class _GdprScreenState extends ConsumerState<GdprScreen> {
  bool _loading = true;
  Map<String, dynamic>? _consentLog;
  Map<String, dynamic>? _exportData;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final userId = ref.read(authProvider).user?.id;
    if (userId == null) {
      setState(() => _loading = false);
      return;
    }

    setState(() => _loading = true);
    try {
      final api = ref.read(apiClientProvider);
      final results = await Future.wait([
        api.get('/users/$userId/consent-log'),
        api.get('/users/$userId/data-export'),
      ]);
      setState(() {
        _consentLog = results[0].data;
        _exportData = results[1].data;
      });
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _requestDeletion() async {
    final userId = ref.read(authProvider).user?.id;
    if (userId == null) return;

    await ref
        .read(apiClientProvider)
        .post('/users/$userId/data-deletion', body: {});
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Deletion request submitted')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('gdpr.title'))),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
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
                            t.t('gdpr.requests'),
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 12),
                          FilledButton.tonalIcon(
                            onPressed: _requestDeletion,
                            icon: const Icon(Icons.delete_outline),
                            label: const Text('Request data deletion'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Current consents',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  ...((_consentLog?['current_consents'] as List<dynamic>? ??
                          const [])
                      .map(
                    (item) => Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        title: Text(item['topic']?.toString() ?? ''),
                        subtitle: Text(item['channel']?.toString() ?? ''),
                        trailing: AppBadge(
                          label: item['status']?.toString() ?? '',
                        ),
                      ),
                    ),
                  )),
                  const SizedBox(height: 16),
                  Text(
                    'Export overview',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(
                        _exportData == null
                            ? 'No export data available'
                            : _exportData!.keys.join(', '),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
