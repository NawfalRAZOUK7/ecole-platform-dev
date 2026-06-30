/// 2FA setup screen — enable/disable 2FA from profile.
///
/// Reference: Phase 5A (from 2B) — 2FA setup in profile
/// Flow: idle → setup (QR + secret) → verify (enter code) → done (backup codes)
/// Disable: enter code → confirm.

import 'package:flutter/material.dart';
import 'package:ecole_platform/shared/ui/widgets/app_snackbar.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

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
  String _provisioningUri = '';
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
        _provisioningUri = data.provisioningUri;
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
          SnackBar(
            content: Text(AppLocalizations.of(ref).t('twoFactor.disabledSnack')),
          ),
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
      SnackBar(content: Text(AppLocalizations.of(ref).t('twoFactor.codesCopied'))),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('twoFactor.title'))),
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

          // ── Idle step ──
          if (_step == _Step.idle) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      t.t('twoFactor.secureAccount'),
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      t.t('twoFactor.secureAccountDesc'),
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        FilledButton.icon(
                          onPressed: _loading ? null : _startSetup,
                          icon: const Icon(Icons.security),
                          label: Text(t.t('twoFactor.enable')),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: () =>
                              setState(() => _step = _Step.disable),
                          child: Text(t.t('common.disable')),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            const SmsTwoFactorCard(),
          ],

          // ── Setup step — show secret ──
          if (_step == _Step.setup) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      t.t('twoFactor.configureApp'),
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      t.t('twoFactor.scanQr'),
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 16),

                    // QR Code rendered locally — the provisioning URI (which
                    // contains the TOTP secret) never leaves the device.
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: theme.colorScheme.outline,
                          width: 1,
                        ),
                      ),
                      child: Column(
                        children: [
                          if (_provisioningUri.isNotEmpty)
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: QrImageView(
                                data: _provisioningUri,
                                version: QrVersions.auto,
                                size: 200,
                                backgroundColor: Colors.white,
                                errorCorrectionLevel: QrErrorCorrectLevel.M,
                              ),
                            )
                          else
                            Icon(
                              Icons.qr_code_2,
                              size: 80,
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          const SizedBox(height: 12),
                          Text(
                            t.t('twoFactor.secretKey'),
                            style: theme.textTheme.labelSmall,
                          ),
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
                              AppSnackBar.success(context, t.t('twoFactor.keyCopied'));
                            },
                            icon: const Icon(Icons.copy, size: 16),
                            label: Text(t.t('twoFactor.copyKey')),
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
                      decoration: InputDecoration(
                        labelText: t.t('auth.verificationCode'),
                        counterText: '',
                        border: const OutlineInputBorder(),
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
                                    color: theme.colorScheme.onPrimary,
                                  ),
                                )
                              : Text(t.t('common.verify')),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: () {
                            setState(() => _step = _Step.idle);
                            _codeController.clear();
                          },
                          child: Text(t.t('common.cancel')),
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
                        Icon(
                          Icons.check_circle,
                          color: theme.colorScheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          t.t('twoFactor.enabledTitle'),
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      t.t('twoFactor.backupCodesDesc'),
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
                            .map(
                              (c) => Padding(
                                padding:
                                    const EdgeInsets.symmetric(vertical: 2),
                                child: Text(
                                  c,
                                  style: const TextStyle(
                                    fontFamily: 'monospace',
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            )
                            .toList(),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        FilledButton.icon(
                          onPressed: _copyBackupCodes,
                          icon: const Icon(Icons.copy),
                          label: Text(t.t('twoFactor.copyCodes')),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: () {
                            if (Navigator.canPop(context)) {
                              Navigator.pop(context);
                            }
                          },
                          child: Text(t.t('common.close')),
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
                    Text(
                      t.t('twoFactor.disableTitle'),
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      t.t('twoFactor.disableDesc'),
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _disableCodeController,
                      decoration: InputDecoration(
                        labelText: t.t('twoFactor.codeOrBackup'),
                        border: const OutlineInputBorder(),
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
                                    color: theme.colorScheme.onPrimary,
                                  ),
                                )
                              : Text(t.t('common.disable')),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          onPressed: () {
                            setState(() => _step = _Step.idle);
                            _disableCodeController.clear();
                          },
                          child: Text(t.t('common.cancel')),
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

/// SMS-based 2FA — alternative / fallback method.
///
/// Flow: idle → enter phone → send OTP → verify → enabled.
/// Calls /auth/sms-2fa/{setup,verify-setup,disable}.
class SmsTwoFactorCard extends ConsumerStatefulWidget {
  const SmsTwoFactorCard({super.key});

  @override
  ConsumerState<SmsTwoFactorCard> createState() => _SmsTwoFactorCardState();
}

enum _SmsStep { idle, enterPhone, verify, disable }

class _SmsTwoFactorCardState extends ConsumerState<SmsTwoFactorCard> {
  _SmsStep _step = _SmsStep.idle;
  bool _loading = false;
  String? _error;
  String _phone = '';
  final _phoneController = TextEditingController();
  final _codeController = TextEditingController();
  final _disableCodeController = TextEditingController();

  @override
  void dispose() {
    _phoneController.dispose();
    _codeController.dispose();
    _disableCodeController.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await action();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _sendCode() async {
    final phone = _phoneController.text.trim();
    if (phone.isEmpty) return;
    await _run(() async {
      await ref.read(authRepositoryProvider).setupSms2fa(phone);
      if (mounted) {
        setState(() {
          _phone = phone;
          _step = _SmsStep.verify;
        });
      }
    });
  }

  Future<void> _verify() async {
    final code = _codeController.text.trim();
    if (code.isEmpty) return;
    await _run(() async {
      await ref.read(authRepositoryProvider).verifySetupSms2fa(code);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(ref).t('twoFactor.smsEnabledSnack')),
          ),
        );
        setState(() => _step = _SmsStep.idle);
      }
    });
  }

  Future<void> _disable() async {
    final code = _disableCodeController.text.trim();
    if (code.isEmpty) return;
    await _run(() async {
      await ref.read(authRepositoryProvider).disableSms2fa(code);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content:
                Text(AppLocalizations.of(ref).t('twoFactor.smsDisabledSnack')),
          ),
        );
        setState(() => _step = _SmsStep.idle);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.sms_outlined, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  t.t('twoFactor.smsTitle'),
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (_error != null) ...[
              Text(
                _error!,
                style: TextStyle(color: theme.colorScheme.error),
              ),
              const SizedBox(height: 8),
            ],
            if (_step == _SmsStep.idle) ...[
              Text(
                t.t('twoFactor.smsDesc'),
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  FilledButton.icon(
                    onPressed: _loading
                        ? null
                        : () => setState(() => _step = _SmsStep.enterPhone),
                    icon: const Icon(Icons.sms),
                    label: Text(t.t('common.enable')),
                  ),
                  const SizedBox(width: 8),
                  OutlinedButton(
                    onPressed: _loading
                        ? null
                        : () => setState(() => _step = _SmsStep.disable),
                    child: Text(t.t('common.disable')),
                  ),
                ],
              ),
            ],
            if (_step == _SmsStep.enterPhone) ...[
              TextField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(
                  labelText: t.t('twoFactor.phoneNumber'),
                  hintText: '+212...',
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  FilledButton(
                    onPressed: _loading ? null : _sendCode,
                    child: _loading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Text(t.t('twoFactor.sendCode')),
                  ),
                  const SizedBox(width: 8),
                  TextButton(
                    onPressed: () => setState(() => _step = _SmsStep.idle),
                    child: Text(t.t('common.cancel')),
                  ),
                ],
              ),
            ],
            if (_step == _SmsStep.verify) ...[
              Text(
                t.t('twoFactor.smsCodeSentTo').replaceAll('{phone}', _phone),
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _codeController,
                keyboardType: TextInputType.number,
                maxLength: 6,
                decoration:
                    InputDecoration(labelText: t.t('twoFactor.code6')),
              ),
              Row(
                children: [
                  FilledButton(
                    onPressed: _loading ? null : _verify,
                    child: Text(t.t('common.verify')),
                  ),
                  const SizedBox(width: 8),
                  TextButton(
                    onPressed: _loading ? null : _sendCode,
                    child: Text(t.t('twoFactor.resend')),
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: () => setState(() => _step = _SmsStep.idle),
                    child: Text(t.t('common.cancel')),
                  ),
                ],
              ),
            ],
            if (_step == _SmsStep.disable) ...[
              Text(
                t.t('twoFactor.smsDisableDesc'),
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _disableCodeController,
                keyboardType: TextInputType.number,
                maxLength: 6,
                decoration:
                    InputDecoration(labelText: t.t('twoFactor.code6')),
              ),
              Row(
                children: [
                  FilledButton(
                    onPressed: _loading ? null : _disable,
                    style: FilledButton.styleFrom(
                      backgroundColor: theme.colorScheme.error,
                    ),
                    child: Text(t.t('common.disable')),
                  ),
                  const SizedBox(width: 8),
                  TextButton(
                    onPressed: () => setState(() => _step = _SmsStep.idle),
                    child: Text(t.t('common.cancel')),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
