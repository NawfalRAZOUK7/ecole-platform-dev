/// Login screen — email, password, school ID + 2FA TOTP step.
///
/// Reference: S-093, UI-CMN-001 — Login flow
/// Phase 5A (from 2B): 2FA verification step with backup code toggle.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'auth_provider.dart';

/// Default school ID from seed data.
const _defaultSchoolId = '00000000-0000-4000-8000-000000000001';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _schoolIdController = TextEditingController(text: _defaultSchoolId);
  final _totpController = TextEditingController();
  bool _useBackupCode = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _schoolIdController.dispose();
    _totpController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    ref.read(authProvider.notifier).clearError();

    await ref.read(authProvider.notifier).login(
          _emailController.text.trim(),
          _passwordController.text,
          _schoolIdController.text.trim(),
        );
    // Navigation is handled by go_router redirect
  }

  Future<void> _handleVerify2fa() async {
    final code = _totpController.text.trim();
    if (code.isEmpty) return;

    ref.read(authProvider.notifier).clearError();
    await ref.read(authProvider.notifier).verify2fa(code);
    // Navigation is handled by go_router redirect
  }

  void _handleCancel2fa() {
    ref.read(authProvider.notifier).cancel2fa();
    _totpController.clear();
    setState(() => _useBackupCode = false);
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final theme = Theme.of(context);

    // 2FA verification step
    if (authState.requires2fa) {
      return Scaffold(
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Icon(Icons.security,
                      size: 64, color: theme.colorScheme.primary),
                  const SizedBox(height: 16),
                  Text(
                    'Vérification 2FA',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _useBackupCode
                        ? 'Entrez un de vos codes de secours.'
                        : 'Entrez le code à 6 chiffres de votre application d\'authentification.',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Error banner
                  if (authState.error != null) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.errorContainer,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.error_outline,
                              color: theme.colorScheme.error, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              authState.error!,
                              style: TextStyle(
                                color: theme.colorScheme.onErrorContainer,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // TOTP / Backup code input
                  TextFormField(
                    controller: _totpController,
                    keyboardType: _useBackupCode
                        ? TextInputType.text
                        : TextInputType.number,
                    maxLength: _useBackupCode ? 20 : 6,
                    textAlign: _useBackupCode ? TextAlign.start : TextAlign.center,
                    style: _useBackupCode
                        ? null
                        : const TextStyle(
                            fontSize: 24,
                            letterSpacing: 8,
                            fontWeight: FontWeight.bold,
                          ),
                    autofillHints: const [AutofillHints.oneTimeCode],
                    decoration: InputDecoration(
                      labelText: _useBackupCode
                          ? 'Code de secours'
                          : 'Code d\'authentification',
                      prefixIcon: Icon(_useBackupCode
                          ? Icons.vpn_key_outlined
                          : Icons.pin_outlined),
                      border: const OutlineInputBorder(),
                      counterText: '',
                    ),
                    enabled: !authState.isLoading,
                  ),
                  const SizedBox(height: 16),

                  // Verify button
                  FilledButton(
                    onPressed: authState.isLoading ? null : _handleVerify2fa,
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: authState.isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Vérifier',
                            style: TextStyle(fontSize: 16)),
                  ),
                  const SizedBox(height: 12),

                  // Toggle backup code / app code
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      TextButton(
                        onPressed: () {
                          setState(() {
                            _useBackupCode = !_useBackupCode;
                            _totpController.clear();
                          });
                        },
                        child: Text(_useBackupCode
                            ? 'Utiliser l\'application'
                            : 'Utiliser un code de secours'),
                      ),
                      TextButton(
                        onPressed: _handleCancel2fa,
                        child: const Text('Annuler'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    }

    // Normal login form
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Logo / Title
                  Icon(
                    Icons.school,
                    size: 64,
                    color: theme.colorScheme.primary,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'École Platform',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Connexion',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Error banner
                  if (authState.error != null) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.errorContainer,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.error_outline,
                              color: theme.colorScheme.error, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              authState.error!,
                              style: TextStyle(
                                color: theme.colorScheme.onErrorContainer,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close, size: 18),
                            onPressed: () =>
                                ref.read(authProvider.notifier).clearError(),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Email field
                  TextFormField(
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.email],
                    decoration: const InputDecoration(
                      labelText: 'Adresse email',
                      prefixIcon: Icon(Icons.email_outlined),
                      border: OutlineInputBorder(),
                    ),
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Email requis' : null,
                    enabled: !authState.isLoading,
                  ),
                  const SizedBox(height: 16),

                  // Password field
                  TextFormField(
                    controller: _passwordController,
                    obscureText: true,
                    autofillHints: const [AutofillHints.password],
                    decoration: const InputDecoration(
                      labelText: 'Mot de passe',
                      prefixIcon: Icon(Icons.lock_outlined),
                      border: OutlineInputBorder(),
                    ),
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Mot de passe requis' : null,
                    enabled: !authState.isLoading,
                  ),
                  const SizedBox(height: 16),

                  // School ID field
                  TextFormField(
                    controller: _schoolIdController,
                    decoration: const InputDecoration(
                      labelText: 'ID Établissement',
                      prefixIcon: Icon(Icons.business),
                      border: OutlineInputBorder(),
                    ),
                    validator: (v) => (v == null || v.isEmpty)
                        ? 'ID établissement requis'
                        : null,
                    enabled: !authState.isLoading,
                  ),
                  const SizedBox(height: 24),

                  // Submit button
                  FilledButton(
                    onPressed: authState.isLoading ? null : _handleLogin,
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: authState.isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Se connecter',
                            style: TextStyle(fontSize: 16)),
                  ),
                  const SizedBox(height: 16),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: authState.isLoading
                          ? null
                          : () => context.push('/forgot-password'),
                      child: const Text('Mot de passe oublié ?'),
                    ),
                  ),

                  // Register link (Phase 5C)
                  Center(
                    child: TextButton(
                      onPressed: () => context.go('/register'),
                      child: const Text(
                        'Vous avez un code d\'invitation ? Inscrivez-vous',
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
