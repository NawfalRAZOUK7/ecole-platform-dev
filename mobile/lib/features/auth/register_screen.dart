/// Registration screen — multi-step: code → info → role fields → OTP.
///
/// Reference: Phase 5C — Registration & Profile Mobile
/// Mirrors web RegisterPage.tsx flow (Phase 4D).
/// Public route (no auth required). After success, navigates to role home.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

part 'register_steps.dart';

const _roleRedirects = <String, String>{
  'PAR': '/feed',
  'STD': '/content',
  'TCH': '/teacher/classes',
  'ADM': '/admin/dashboard',
  'DIR': '/admin/dashboard',
  'SUP': '/notifications',
};

const _passwordRules = <String, String>{
  'minLength': '12 caractères minimum',
  'uppercase': 'Une lettre majuscule',
  'lowercase': 'Une lettre minuscule',
  'digit': 'Un chiffre',
  'special': 'Un caractère spécial',
};

bool _checkRule(String key, String password) {
  switch (key) {
    case 'minLength':
      return password.length >= 12;
    case 'uppercase':
      return password.contains(RegExp(r'[A-Z]'));
    case 'lowercase':
      return password.contains(RegExp(r'[a-z]'));
    case 'digit':
      return password.contains(RegExp(r'\d'));
    case 'special':
      return password.contains(RegExp(r'[^A-Za-z0-9]'));
    default:
      return false;
  }
}

bool _allRulesPassed(String password) {
  return _passwordRules.keys.every((k) => _checkRule(k, password));
}

const _relationshipTypes = ['father', 'mother', 'guardian', 'other'];
const _relationshipLabels = {
  'father': 'Père',
  'mother': 'Mère',
  'guardian': 'Tuteur',
  'other': 'Autre',
};

enum _Step { code, info, role, otp }

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  _Step _step = _Step.code;
  bool _loading = false;
  String? _error;

  // Step 1 — code
  final _codeController = TextEditingController();

  // Step 2 — personal info
  final _emailController = TextEditingController();
  final _fullNameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  // Step 3 — role fields
  final _dobController = TextEditingController();
  final _classLevelController = TextEditingController();
  String _relationshipType = '';
  final _subjectController = TextEditingController();
  final _qualificationController = TextEditingController();

  // Step 4 — OTP
  final _otpController = TextEditingController();
  String _userId = '';
  String _schoolId = '';
  String _registeredRole = '';

  @override
  void dispose() {
    _codeController.dispose();
    _emailController.dispose();
    _fullNameController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _dobController.dispose();
    _classLevelController.dispose();
    _subjectController.dispose();
    _qualificationController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  void _setError(String? error) => setState(() => _error = error);
  void _applyState(VoidCallback update) => setState(update);

  // Step 1: Validate code format
  void _handleCodeSubmit() {
    _setError(null);
    final code = _codeController.text.trim();
    if (code.length != 8) {
      _setError('Code invalide ou expiré');
      return;
    }
    setState(() => _step = _Step.info);
  }

  // Step 2: Validate personal info
  void _handleInfoSubmit() {
    _setError(null);
    final password = _passwordController.text;
    final confirm = _confirmPasswordController.text;

    if (password != confirm) {
      _setError('Les mots de passe ne correspondent pas');
      return;
    }
    if (!_allRulesPassed(password)) {
      _setError('Le mot de passe ne respecte pas les exigences');
      return;
    }
    setState(() => _step = _Step.role);
  }

  // Step 3: Submit registration
  Future<void> _handleRoleSubmit() async {
    _setError(null);
    setState(() => _loading = true);

    final profileData = <String, String>{};
    if (_dobController.text.isNotEmpty) {
      profileData['date_of_birth'] = _dobController.text;
    }
    if (_classLevelController.text.isNotEmpty) {
      profileData['class_level'] = _classLevelController.text;
    }
    if (_relationshipType.isNotEmpty) {
      profileData['relationship_type'] = _relationshipType;
    }
    if (_subjectController.text.isNotEmpty) {
      profileData['subject_specialty'] = _subjectController.text;
    }
    if (_qualificationController.text.isNotEmpty) {
      profileData['qualification'] = _qualificationController.text;
    }

    try {
      final repo = ref.read(authRepositoryProvider);
      final result = await repo.register(
        code: _codeController.text.trim(),
        email: _emailController.text.trim(),
        fullName: _fullNameController.text.trim(),
        phone: _phoneController.text.trim(),
        password: _passwordController.text,
        profileData: profileData,
      );

      _userId = result.userId;
      _schoolId = result.schoolId;
      _registeredRole = result.role;

      if (result.emailVerificationRequired) {
        setState(() {
          _step = _Step.otp;
          _loading = false;
        });
      } else {
        _navigateToHome();
      }
    } on ApiClientError catch (e) {
      setState(() {
        _error = e.apiError.message;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Une erreur est survenue';
        _loading = false;
      });
    }
  }

  // Step 4: Verify OTP
  Future<void> _handleOtpSubmit() async {
    _setError(null);
    setState(() => _loading = true);

    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.verifyEmail(
        userId: _userId,
        schoolId: _schoolId,
        otp: _otpController.text.trim(),
      );
      _navigateToHome();
    } on ApiClientError catch (e) {
      setState(() {
        _error = e.apiError.message;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Une erreur est survenue';
        _loading = false;
      });
    }
  }

  void _navigateToHome() {
    final target = _roleRedirects[_registeredRole] ?? '/profile';
    context.go(target);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final steps = _Step.values;
    final stepIndex = steps.indexOf(_step);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                Icon(Icons.school, size: 64, color: theme.colorScheme.primary),
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
                  'Créer un compte',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 24),

                // Step indicator
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(steps.length, (i) {
                    return Container(
                      width: 40,
                      height: 4,
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(2),
                        color: i <= stepIndex
                            ? theme.colorScheme.primary
                            : theme.colorScheme.outlineVariant,
                      ),
                    );
                  }),
                ),
                const SizedBox(height: 24),

                // Error banner
                if (_error != null) ...[
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
                            _error!,
                            style: TextStyle(
                              color: theme.colorScheme.onErrorContainer,
                              fontSize: 13,
                            ),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close, size: 18),
                          onPressed: () => _setError(null),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // Step content
                if (_step == _Step.code) _buildCodeStep(theme),
                if (_step == _Step.info) _buildInfoStep(theme),
                if (_step == _Step.role) _buildRoleStep(theme),
                if (_step == _Step.otp) _buildOtpStep(theme),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
