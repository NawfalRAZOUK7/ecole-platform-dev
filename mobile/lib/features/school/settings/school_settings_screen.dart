import 'package:flutter/material.dart';
import 'package:ecole_platform/shared/ui/widgets/app_snackbar.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class SchoolSettingsScreen extends ConsumerStatefulWidget {
  const SchoolSettingsScreen({super.key});

  @override
  ConsumerState<SchoolSettingsScreen> createState() =>
      _SchoolSettingsScreenState();
}

class _SchoolSettingsScreenState extends ConsumerState<SchoolSettingsScreen> {
  final _nameController = TextEditingController();
  final _addressController = TextEditingController();
  final _phoneController = TextEditingController();
  final _timezoneController = TextEditingController(text: 'Africa/Casablanca');
  final _currencyController = TextEditingController(text: 'MAD');
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _addressController.dispose();
    _phoneController.dispose();
    _timezoneController.dispose();
    _currencyController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final response = await ref.read(apiClientProvider).get('/admin/school');
      _nameController.text = response.data['name'] as String? ?? '';
      _addressController.text = response.data['address'] as String? ?? '';
      _phoneController.text = response.data['phone'] as String? ?? '';
      _timezoneController.text =
          response.data['timezone'] as String? ?? _timezoneController.text;
      _currencyController.text =
          response.data['currency'] as String? ?? _currencyController.text;
    } catch (_) {
      // Keep defaults when endpoint is unavailable.
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
        '/admin/school',
        body: {
          'name': _nameController.text.trim(),
          'address': _addressController.text.trim(),
          'phone': _phoneController.text.trim(),
          'timezone': _timezoneController.text.trim(),
          'currency': _currencyController.text.trim(),
        },
      );
      if (!mounted) return;
      AppSnackBar.success(context, 'School settings saved');
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

    final t = AppLocalizations.of(ref);
    return Scaffold(
      appBar: AppBar(title: Text(t.t('admin.schoolSettings'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _nameController,
            decoration: InputDecoration(labelText: t.t('school.name')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _addressController,
            maxLines: 2,
            decoration: InputDecoration(labelText: t.t('school.address')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _phoneController,
            decoration: InputDecoration(labelText: t.t('school.phone')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _timezoneController,
            decoration: InputDecoration(labelText: t.t('school.timezone')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _currencyController,
            decoration: InputDecoration(labelText: t.t('school.currency')),
          ),
        ],
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
          label: Text(t.t('school.saveSettings')),
        ),
      ),
    );
  }
}
