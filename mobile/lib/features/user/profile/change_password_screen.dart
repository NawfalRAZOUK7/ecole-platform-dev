/// Change password screen — enter current + new password.
///
/// Reference: Phase 5A — Password change from profile
/// Policy: 12+ chars, uppercase, lowercase, digit, special char.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class ChangePasswordScreen extends ConsumerStatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  ConsumerState<ChangePasswordScreen> createState() =>
      _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends ConsumerState<ChangePasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _currentController = TextEditingController();
  final _newController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _currentController.dispose();
    _newController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  String? _validatePassword(String? value) {
    final t = AppLocalizations.of(ref);
    if (value == null || value.isEmpty) {
      return t.t('passwordValidation.required');
    }
    if (value.length < 12) return t.t('passwordValidation.minLength');
    if (!value.contains(RegExp(r'[A-Z]'))) {
      return t.t('passwordValidation.uppercase');
    }
    if (!value.contains(RegExp(r'[a-z]'))) {
      return t.t('passwordValidation.lowercase');
    }
    if (!value.contains(RegExp(r'[0-9]'))) {
      return t.t('passwordValidation.digit');
    }
    if (!value.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'))) {
      return t.t('passwordValidation.special');
    }
    return null;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (_newController.text != _confirmController.text) {
      setState(() => _error = 'Les mots de passe ne correspondent pas');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.changePassword(
        _currentController.text,
        _newController.text,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content:
                Text(AppLocalizations.of(ref).t('changePassword.success')),
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('profile.changePassword'))),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          if (_error != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: theme.colorScheme.errorContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _error!,
                style: TextStyle(color: theme.colorScheme.onErrorContainer),
              ),
            ),
            const SizedBox(height: 16),
          ],
          Form(
            key: _formKey,
            child: Column(
              children: [
                TextFormField(
                  controller: _currentController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: t.t('changePassword.current'),
                    prefixIcon: const Icon(Icons.lock_outline),
                    border: const OutlineInputBorder(),
                  ),
                  validator: (v) =>
                      (v == null || v.isEmpty) ? t.t('common.required') : null,
                  enabled: !_loading,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _newController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: t.t('auth.newPassword'),
                    prefixIcon: const Icon(Icons.lock),
                    border: const OutlineInputBorder(),
                    helperText: t.t('changePassword.helper'),
                    helperMaxLines: 2,
                  ),
                  validator: _validatePassword,
                  enabled: !_loading,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _confirmController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: t.t('changePassword.confirmNew'),
                    prefixIcon: const Icon(Icons.lock),
                    border: const OutlineInputBorder(),
                  ),
                  validator: (v) {
                    if (v == null || v.isEmpty) return t.t('common.required');
                    if (v != _newController.text) {
                      return t.t('register.passwordMismatch');
                    }
                    return null;
                  },
                  enabled: !_loading,
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _loading ? null : _submit,
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    minimumSize: const Size(double.infinity, 0),
                  ),
                  child: _loading
                      ? SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Theme.of(context).colorScheme.onPrimary,
                          ),
                        )
                      : Text(
                          t.t('profile.changePassword'),
                          style: const TextStyle(fontSize: 16),
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
