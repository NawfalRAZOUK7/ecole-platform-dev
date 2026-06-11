/// ActivateScreen — public set-password screen for onboarding-provisioned
/// owners (no auth).
///
/// Reached via the activation link emailed on SuperAdmin approval
/// (`/activate?token=…`). The owner chooses a password; a valid submission
/// flips their INACTIVE account to ACTIVE via `POST /auth/activate` (skipAuth),
/// after which they can log in. Localized (fr/en/ar).

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class ActivateScreen extends ConsumerStatefulWidget {
  final String? token;
  const ActivateScreen({super.key, this.token});

  @override
  ConsumerState<ActivateScreen> createState() => _ActivateScreenState();
}

class _ActivateScreenState extends ConsumerState<ActivateScreen> {
  bool _submitting = false;
  bool _done = false;
  String? _error;

  final _password = TextEditingController();
  final _confirm = TextEditingController();

  @override
  void dispose() {
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit(String Function(String, String, String) tr) async {
    final pw = _password.text;
    if (pw.length < 12) {
      setState(() => _error = tr(
            'Le mot de passe doit contenir au moins 12 caractères.',
            'Password must be at least 12 characters.',
            'يجب أن تتكون كلمة المرور من 12 حرفًا على الأقل.',
          ),);
      return;
    }
    if (pw != _confirm.text) {
      setState(() => _error = tr(
            'Les mots de passe ne correspondent pas.',
            'Passwords do not match.',
            'كلمتا المرور غير متطابقتين.',
          ),);
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).post(
        '/auth/activate',
        body: {'token': widget.token, 'password': pw},
        skipAuth: true,
      );
      if (mounted) setState(() => _done = true);
    } catch (e) {
      if (mounted) {
        setState(() => _error = tr(
              "L'activation a échoué. Le lien est peut-être expiré ou déjà utilisé.",
              'Activation failed. The link may be expired or already used.',
              'فشل التفعيل. قد يكون الرابط منتهي الصلاحية أو مستخدمًا من قبل.',
            ),);
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final locale = ref.watch(localeProvider);
    String tr(String fr, String en, String ar) =>
        locale == 'ar' ? ar : (locale == 'en' ? en : fr);

    if (widget.token == null || widget.token!.isEmpty) {
      return Scaffold(
        appBar: AppBar(
          title: Text(tr('Activer le compte', 'Activate account', 'تفعيل الحساب')),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  tr(
                    "Lien d'activation invalide ou incomplet.",
                    'Invalid or incomplete activation link.',
                    'رابط التفعيل غير صالح أو غير مكتمل.',
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: () => context.go('/login'),
                  child: Text(tr('Connexion', 'Log in', 'تسجيل الدخول')),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (_done) {
      return Scaffold(
        appBar: AppBar(
          title: Text(tr('Compte activé', 'Account activated', 'تم التفعيل')),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('✅', style: TextStyle(fontSize: 56)),
                const SizedBox(height: 12),
                Text(
                  tr(
                    'Votre mot de passe a été défini et votre compte est actif. Vous pouvez maintenant vous connecter.',
                    'Your password has been set and your account is active. You can now log in.',
                    'تم تعيين كلمة المرور وحسابك الآن نشط. يمكنك تسجيل الدخول.',
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: () => context.go('/login'),
                  child: Text(tr('Se connecter', 'Log in', 'تسجيل الدخول')),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(tr('Activer votre compte', 'Activate your account', 'تفعيل حسابك')),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            tr(
              'Choisissez un mot de passe pour finaliser votre compte.',
              'Choose a password to finish setting up your account.',
              'اختر كلمة مرور لإكمال إعداد حسابك.',
            ),
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _password,
            obscureText: true,
            decoration: InputDecoration(
              labelText: tr('Mot de passe', 'Password', 'كلمة المرور'),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _confirm,
            obscureText: true,
            decoration: InputDecoration(
              labelText: tr(
                'Confirmer le mot de passe',
                'Confirm password',
                'تأكيد كلمة المرور',
              ),
              border: const OutlineInputBorder(),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _submitting ? null : () => _submit(tr),
            child: Text(
              _submitting
                  ? tr('Activation…', 'Activating…', 'جارٍ التفعيل…')
                  : tr('Activer le compte', 'Activate account', 'تفعيل الحساب'),
            ),
          ),
        ],
      ),
    );
  }
}
