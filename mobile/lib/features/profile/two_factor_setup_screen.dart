/// 2FA setup screen — enable/disable 2FA from profile.
///
/// Reference: Phase 5A (from 2B) — 2FA setup in profile
/// Flow: idle → setup (QR + secret) → verify (enter code) → done (backup codes)
/// Disable: enter code → confirm.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';

enum _Step { idle, setup, done, disable }

class TwoFactorSetupScreen extends ConsumerStatefulWidget {
  const TwoFactorSetupScreen({super.key});

  @override
  ConsumerState<TwoFactorSetupScreen> createState() =>
      _TwoFactorSetupScreenState();
}

class _TwoFactorSetupScreenState extends ConsumerState<TwoFactorSetupScreen> {
  _Step _step = _Step.idle;
  bool _loading = false;
  String? _error;

  // Setup state
  String _secret = '';
  final _codeController = TextEditingController();
  List<String> _backupCodes = [];

  // Disable state
  final _disableCodeController = TextEditingController();

  @override
  void dispose() {
    _codeController.dispose();
    _disableCodeController.dispose();
    super.dispose();
  }

  Future<void> _startSetup() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = ref.read(authRepositoryProvider);
      final data = await repo.setup2fa();
      setState(() {
        _secret = data.secret;
        _step = _Step.setup;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _verifySetup() async {
    final code = _codeController.text.trim();
    if (code.isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = ref.read(authRepositoryProvider);
      final result = await repo.verifySetup2fa(code);
      setState(() {
        _backupCodes = result.backupCodes;
        _step = _Step.done;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _disable2fa() async {
    final code = _disableCodeController.text.trim();
    if (code.isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.disable2fa(code);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('2FA désactivée')),
        );
        setState(() => _step = _Step.idle);
        _disableCodeController.clear();
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  void _copyBackupCodes() {
    Clipboard.setData(ClipboardData(text: _backupCodes.join('\n')));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Codes copiés dans le presse-papiers')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Authentification 2FA')),
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
              child: Text(_error!,
                  style: TextStyle(color: theme.colorScheme.onErrorContainer)),
            ),
            const SizedBox(height: 16),
          ],

          // ── Idle step ──
          if (_step == _Step.idle) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Sécurisez votre compte',
                        style: theme.textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text(
                      'Ajoutez une couche de sécurité supplémentaire avec une application d\'authentification (Google Authenticator, Authy, etc.)',
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        FilledButton.icon(
                          onPressed: _loading ? null : _startSetup,
                          icon: const Icon(Icons.security),
                          label: const Text('Activer la 2FA'),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: () =>
                              setState(() => _step = _Step.disable),
                          child: const Text('Désactiver'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],

          // ── Setup step — show secret ──
          if (_step == _Step.setup) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Configurer l\'application',
                        style: theme.textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text(
                      'Scannez le QR code ou entrez la clé manuellement dans votre application d\'authentification.',
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 16),

                    // QR Code placeholder (mobile can't render QR inline easily without a package,
                    // but we show the provisioning URI for copy and the secret for manual entry)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                            color: theme.colorScheme.outline, width: 1),
                      ),
                      child: Column(
                        children: [
                          Icon(Icons.qr_code_2,
                              size: 80,
                              color: theme.colorScheme.onSurfaceVariant),
                          const SizedBox(height: 8),
                          Text('Clé secrète :',
                              style: theme.textTheme.labelSmall),
                          const SizedBox(height: 4),
                          SelectableText(
                            _secret,
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              letterSpacing: 2,
                              color: theme.colorScheme.primary,
                            ),
                          ),
                          const SizedBox(height: 8),
                          TextButton.icon(
                            onPressed: () {
                              Clipboard.setData(ClipboardData(text: _secret));
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Clé copiée')),
                              );
                            },
                            icon: const Icon(Icons.copy, size: 16),
                            label: const Text('Copier la clé'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Verify code
                    TextFormField(
                      controller: _codeController,
                      keyboardType: TextInputType.number,
                      maxLength: 6,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 24,
                        letterSpacing: 8,
                        fontWeight: FontWeight.bold,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Code de vérification',
                        counterText: '',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        FilledButton(
                          onPressed: _loading ? null : _verifySetup,
                          child: _loading
                              ? SizedBox(
                                  height: 16,
                                  width: 16,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: theme.colorScheme.onPrimary))
                              : const Text('Vérifier'),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: () {
                            setState(() => _step = _Step.idle);
                            _codeController.clear();
                          },
                          child: const Text('Annuler'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],

          // ── Done step — backup codes ──
          if (_step == _Step.done) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.check_circle,
                            color: theme.colorScheme.primary),
                        const SizedBox(width: 8),
                        Text('2FA activée !',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: theme.colorScheme.primary,
                            )),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Sauvegardez ces codes de secours. Chaque code ne peut être utilisé qu\'une seule fois.',
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: _backupCodes
                            .map((c) => Padding(
                                  padding:
                                      const EdgeInsets.symmetric(vertical: 2),
                                  child: Text(c,
                                      style: const TextStyle(
                                        fontFamily: 'monospace',
                                        fontSize: 16,
                                        fontWeight: FontWeight.w600,
                                      )),
                                ))
                            .toList(),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        FilledButton.icon(
                          onPressed: _copyBackupCodes,
                          icon: const Icon(Icons.copy),
                          label: const Text('Copier les codes'),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: () {
                            if (Navigator.canPop(context)) {
                              Navigator.pop(context);
                            }
                          },
                          child: const Text('Fermer'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],

          // ── Disable step ──
          if (_step == _Step.disable) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Désactiver la 2FA',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        )),
                    const SizedBox(height: 8),
                    Text(
                      'Entrez votre code d\'authentification ou un code de secours pour désactiver la 2FA.',
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _disableCodeController,
                      decoration: const InputDecoration(
                        labelText: 'Code ou code de secours',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        FilledButton(
                          onPressed: _loading ? null : _disable2fa,
                          style: FilledButton.styleFrom(
                            backgroundColor: theme.colorScheme.error,
                          ),
                          child: _loading
                              ? SizedBox(
                                  height: 16,
                                  width: 16,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: theme.colorScheme.onPrimary))
                              : const Text('Désactiver'),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: () {
                            setState(() => _step = _Step.idle);
                            _disableCodeController.clear();
                          },
                          child: const Text('Annuler'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
