import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';

class FeatureTogglesScreen extends ConsumerStatefulWidget {
  const FeatureTogglesScreen({super.key});

  @override
  ConsumerState<FeatureTogglesScreen> createState() =>
      _FeatureTogglesScreenState();
}

class _FeatureTogglesScreenState extends ConsumerState<FeatureTogglesScreen> {
  Map<String, bool> _toggles = {
    'attendance': true,
    'gradebook': true,
    'budgets': true,
    'micro_schools': true,
    'offline_sync': true,
  };
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final response = await ref.read(apiClientProvider).get('/admin/features');
      _toggles = (response.data['features'] as Map<String, dynamic>? ?? {})
          .map((key, value) => MapEntry(key, value as bool? ?? false));
    } catch (_) {
      // Keep fallback defaults when endpoint is unavailable.
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ref.read(apiClientProvider).put(
        '/admin/features',
        body: {'features': _toggles},
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Feature toggles saved')),
      );
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Feature toggles')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: _toggles.entries
            .map(
              (entry) => Card(
                child: SwitchListTile(
                  title: Text(entry.key.replaceAll('_', ' ')),
                  value: entry.value,
                  onChanged: (value) {
                    setState(() => _toggles[entry.key] = value);
                  },
                ),
              ),
            )
            .toList(),
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.all(16),
        child: FilledButton.icon(
          onPressed: _saving ? null : _save,
          icon: _saving
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.save_outlined),
          label: const Text('Save toggles'),
        ),
      ),
    );
  }
}
