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
import 'package:ecole_platform/domain/repositories/auth_repository.dart';

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

  // ── Step 1: Code ──
  Widget _buildCodeStep(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Entrez votre code d\'invitation',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 24),
        TextFormField(
          controller: _codeController,
          textCapitalization: TextCapitalization.characters,
          maxLength: 8,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 20, letterSpacing: 6),
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Code d\'invitation',
            prefixIcon: Icon(Icons.confirmation_number_outlined),
            border: OutlineInputBorder(),
            counterText: '',
          ),
          enabled: !_loading,
        ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: _loading || _codeController.text.length != 8
              ? null
              : _handleCodeSubmit,
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: const Text('Suivant', style: TextStyle(fontSize: 16)),
        ),
        const SizedBox(height: 16),
        Center(
          child: TextButton(
            onPressed: () => context.go('/login'),
            child: const Text('Vous avez déjà un compte ? Connectez-vous'),
          ),
        ),
      ],
    );
  }

  // ── Step 2: Personal Info ──
  Widget _buildInfoStep(ThemeData theme) {
    final password = _passwordController.text;
    final confirm = _confirmPasswordController.text;
    final canProceed = _emailController.text.isNotEmpty &&
        _fullNameController.text.isNotEmpty &&
        password.isNotEmpty &&
        _allRulesPassed(password) &&
        password == confirm;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Vos informations personnelles',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 20),
        TextFormField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          autofillHints: const [AutofillHints.email],
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Adresse email',
            prefixIcon: Icon(Icons.email_outlined),
            border: OutlineInputBorder(),
          ),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _fullNameController,
          textCapitalization: TextCapitalization.words,
          decoration: const InputDecoration(
            labelText: 'Nom complet',
            prefixIcon: Icon(Icons.person_outlined),
            border: OutlineInputBorder(),
          ),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _phoneController,
          keyboardType: TextInputType.phone,
          decoration: const InputDecoration(
            labelText: 'Téléphone (optionnel)',
            prefixIcon: Icon(Icons.phone_outlined),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _passwordController,
          obscureText: true,
          autofillHints: const [AutofillHints.newPassword],
          decoration: const InputDecoration(
            labelText: 'Mot de passe',
            prefixIcon: Icon(Icons.lock_outlined),
            border: OutlineInputBorder(),
          ),
          onChanged: (_) => setState(() {}),
        ),
        // Password policy checklist
        if (password.isNotEmpty) ...[
          const SizedBox(height: 8),
          ...(_passwordRules.entries.map((e) {
            final passed = _checkRule(e.key, password);
            return Padding(
              padding: const EdgeInsets.only(left: 8, bottom: 2),
              child: Row(
                children: [
                  Icon(
                    passed ? Icons.check_circle : Icons.cancel,
                    size: 14,
                    color: passed ? Colors.green : Colors.red,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    e.value,
                    style: TextStyle(
                      fontSize: 12,
                      color: passed ? Colors.green : Colors.red,
                    ),
                  ),
                ],
              ),
            );
          })),
        ],
        const SizedBox(height: 12),
        TextFormField(
          controller: _confirmPasswordController,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Confirmer le mot de passe',
            prefixIcon: Icon(Icons.lock_outlined),
            border: OutlineInputBorder(),
          ),
          onChanged: (_) => setState(() {}),
        ),
        if (confirm.isNotEmpty && password != confirm) ...[
          const SizedBox(height: 4),
          const Padding(
            padding: EdgeInsets.only(left: 8),
            child: Text(
              'Les mots de passe ne correspondent pas',
              style: TextStyle(fontSize: 12, color: Colors.red),
            ),
          ),
        ],
        const SizedBox(height: 20),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () => setState(() => _step = _Step.code),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Retour'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              flex: 2,
              child: FilledButton(
                onPressed: canProceed ? _handleInfoSubmit : null,
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Suivant', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ── Step 3: Role-specific fields ──
  Widget _buildRoleStep(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Informations complémentaires (remplissez ce qui correspond à votre rôle)',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 20),

        // Date of birth
        TextFormField(
          controller: _dobController,
          readOnly: true,
          decoration: const InputDecoration(
            labelText: 'Date de naissance',
            prefixIcon: Icon(Icons.calendar_today),
            border: OutlineInputBorder(),
          ),
          onTap: () async {
            final date = await showDatePicker(
              context: context,
              initialDate: DateTime(2005, 1, 1),
              firstDate: DateTime(1940),
              lastDate: DateTime.now(),
            );
            if (date != null) {
              _dobController.text =
                  '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
            }
          },
        ),
        const SizedBox(height: 12),

        // Class level
        TextFormField(
          controller: _classLevelController,
          decoration: const InputDecoration(
            labelText: 'Niveau scolaire',
            prefixIcon: Icon(Icons.school_outlined),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),

        // Relationship type (parent)
        DropdownButtonFormField<String>(
          value: _relationshipType.isEmpty ? null : _relationshipType,
          decoration: const InputDecoration(
            labelText: 'Lien de parenté',
            prefixIcon: Icon(Icons.family_restroom),
            border: OutlineInputBorder(),
          ),
          items: [
            const DropdownMenuItem(value: '', child: Text('Sélectionner (optionnel)')),
            ..._relationshipTypes.map((rt) => DropdownMenuItem(
                  value: rt,
                  child: Text(_relationshipLabels[rt] ?? rt),
                )),
          ],
          onChanged: (v) => setState(() => _relationshipType = v ?? ''),
        ),
        const SizedBox(height: 12),

        // Subject specialty (teacher)
        TextFormField(
          controller: _subjectController,
          decoration: const InputDecoration(
            labelText: 'Spécialité',
            prefixIcon: Icon(Icons.book_outlined),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),

        // Qualification (teacher)
        TextFormField(
          controller: _qualificationController,
          decoration: const InputDecoration(
            labelText: 'Diplôme / Qualification',
            prefixIcon: Icon(Icons.workspace_premium_outlined),
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 24),

        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: _loading
                    ? null
                    : () => setState(() => _step = _Step.info),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Retour'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              flex: 2,
              child: FilledButton(
                onPressed: _loading ? null : _handleRoleSubmit,
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: _loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Créer le compte',
                        style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ── Step 4: OTP ──
  Widget _buildOtpStep(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Entrez le code à 6 chiffres envoyé à votre adresse email',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 24),
        TextFormField(
          controller: _otpController,
          keyboardType: TextInputType.number,
          maxLength: 6,
          textAlign: TextAlign.center,
          autofocus: true,
          style: const TextStyle(
            fontSize: 24,
            letterSpacing: 8,
            fontWeight: FontWeight.bold,
          ),
          decoration: const InputDecoration(
            labelText: 'Code de vérification',
            prefixIcon: Icon(Icons.pin_outlined),
            border: OutlineInputBorder(),
            counterText: '',
          ),
          enabled: !_loading,
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed:
              _loading || _otpController.text.length != 6 ? null : _handleOtpSubmit,
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: _loading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: Colors.white),
                )
              : const Text('Vérifier', style: TextStyle(fontSize: 16)),
        ),
        const SizedBox(height: 8),
        Center(
          child: TextButton(
            onPressed: _navigateToHome,
            child: const Text(
              'Passer pour l\'instant',
              style: TextStyle(color: Colors.grey),
            ),
          ),
        ),
      ],
    );
  }
}
