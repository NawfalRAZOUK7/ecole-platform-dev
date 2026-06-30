/// Profile screen — user info, role-specific profile, security settings, logout.
///
/// Reference: UI-CMN-001 — Profile screen
/// Phase 5A: 2FA setup navigation + biometric toggle switch.
/// Phase 5C: Role-specific profile sections (student/parent/teacher).
/// Phase 10C: Teacher reward points display.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/taxonomy/taxonomy.g.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

const _roleLabels = {
  'ADM': 'Administrateur',
  'DIR': 'Directeur',
  'TCH': 'Enseignant',
  'PAR': 'Parent',
  'STD': 'Élève',
  'SUP': 'Support',
  'SYS': 'Système',
};

const _relationshipLabels = {
  'father': 'Père',
  'mother': 'Mère',
  'guardian': 'Tuteur',
  'other': 'Autre',
};

const _relationshipTypes = ['father', 'mother', 'guardian', 'other'];
const _themeModeLabels = {
  ThemeMode.system: 'Système',
  ThemeMode.light: 'Clair',
  ThemeMode.dark: 'Sombre',
};
const _localeLabels = {
  'fr': 'Français',
  'ar': 'العربية',
  'en': 'English',
};

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  Map<String, dynamic>? _profileData;
  bool _profileLoading = true;
  String? _profileError;
  bool _editing = false;
  bool _saving = false;
  String? _saveSuccess;

  // Edit controllers — initialized from profile data
  final _dobController = TextEditingController();
  String _classLevel = '';
  String _relationshipType = '';
  final _cinController = TextEditingController();
  final _emergencyPhoneController = TextEditingController();
  String _subjectSpecialty = '';
  final _qualificationController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchProfile();
  }

  @override
  void dispose() {
    _dobController.dispose();
    _cinController.dispose();
    _emergencyPhoneController.dispose();
    _qualificationController.dispose();
    super.dispose();
  }

  Future<void> _fetchProfile() async {
    setState(() {
      _profileLoading = true;
      _profileError = null;
    });
    try {
      final repo = ref.read(authRepositoryProvider);
      final data = await repo.getProfile();
      setState(() {
        _profileData = data;
        _profileLoading = false;
        _populateEditFields(data);
      });
    } catch (e) {
      setState(() {
        _profileLoading = false;
        _profileError = 'Impossible de charger le profil';
      });
    }
  }

  void _populateEditFields(Map<String, dynamic> data) {
    // Nested profile data may be under role-specific keys
    final student = data['student_profile'] as Map<String, dynamic>?;
    final parent = data['parent_profile'] as Map<String, dynamic>?;
    final teacher = data['teacher_profile'] as Map<String, dynamic>?;

    _dobController.text = student?['date_of_birth'] as String? ?? '';
    final classLevel = student?['class_level'] as String? ?? '';
    _classLevel = Taxonomy.levelBands.contains(classLevel) ? classLevel : '';
    _relationshipType = parent?['relationship_type'] as String? ?? '';
    _cinController.text = parent?['cin_number'] as String? ?? '';
    _emergencyPhoneController.text =
        parent?['emergency_phone'] as String? ?? '';
    final specialty = teacher?['subject_specialty'] as String? ?? '';
    _subjectSpecialty = Taxonomy.subjects.contains(specialty) ? specialty : '';
    _qualificationController.text = teacher?['qualification'] as String? ?? '';
  }

  Future<void> _saveProfile() async {
    setState(() {
      _saving = true;
      _saveSuccess = null;
    });

    final body = <String, dynamic>{};
    if (_dobController.text.isNotEmpty) {
      body['date_of_birth'] = _dobController.text;
    }
    if (_classLevel.isNotEmpty) {
      body['class_level'] = _classLevel;
    }
    if (_relationshipType.isNotEmpty) {
      body['relationship_type'] = _relationshipType;
    }
    if (_cinController.text.isNotEmpty) {
      body['cin_number'] = _cinController.text;
    }
    if (_emergencyPhoneController.text.isNotEmpty) {
      body['emergency_phone'] = _emergencyPhoneController.text;
    }
    if (_subjectSpecialty.isNotEmpty) {
      body['subject_specialty'] = _subjectSpecialty;
    }
    if (_qualificationController.text.isNotEmpty) {
      body['qualification'] = _qualificationController.text;
    }

    try {
      final repo = ref.read(authRepositoryProvider);
      final updated = await repo.updateProfile(body);
      setState(() {
        _profileData = updated;
        _saving = false;
        _editing = false;
        _saveSuccess = 'Profil enregistré';
        _populateEditFields(updated);
      });
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) setState(() => _saveSuccess = null);
      });
    } catch (e) {
      setState(() {
        _saving = false;
        _profileError = 'Erreur lors de la sauvegarde';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    final theme = Theme.of(context);
    final themeMode = ref.watch(themeModeProvider);
    final localeCode = ref.watch(localeProvider);
    final t = AppLocalizations.of(ref);

    if (user == null) return const SizedBox.shrink();

    return Scaffold(
      appBar: AppBar(title: Text(t.t('profile.title'))),
      body: Semantics(
        container: true,
        label: 'Profil utilisateur',
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            // Profile hero
            Semantics(
              label: 'Profil de ${user.fullName}',
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  gradient: const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Color(0xFF2563EB),
                      Color(0xFF5B5BEF),
                      Color(0xFF8B5CF6),
                    ],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.12),
                      blurRadius: 18,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 36,
                      backgroundColor: Colors.white,
                      child: Text(
                        user.fullName.isNotEmpty
                            ? user.fullName[0].toUpperCase()
                            : '?',
                        style: const TextStyle(
                          fontSize: 30,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF2563EB),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            user.fullName,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.2),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Text(
                              _roleLabels[user.role] ?? user.role,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),

            // Info cards
            _InfoTile(
              icon: Icons.email_outlined,
              label: 'Email',
              value: user.email,
            ),
            _InfoTile(
              icon: Icons.business,
              label: 'Établissement',
              value: user.schoolId,
            ),
            const SizedBox(height: 16),

            // Permissions (réservé aux rôles d'administration)
            if ((user.role == 'SUP' || user.role == 'ADM') &&
                user.permissions.isNotEmpty) ...[
              Text(
                'Permissions',
                style: theme.textTheme.titleSmall
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: user.permissions
                    .map(
                      (p) => Chip(
                        label: Text(p, style: const TextStyle(fontSize: 10)),
                        padding: EdgeInsets.zero,
                        visualDensity: VisualDensity.compact,
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    )
                    .toList(),
              ),
              const SizedBox(height: 24),
            ],

            // ── Role-specific profile section (Phase 5C) ──
            if (['STD', 'PAR', 'TCH'].contains(user.role))
              _buildRoleProfileSection(theme, user.role),

            // Success banner
            if (_saveSuccess != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.semanticPalette.successContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.check_circle,
                      color: theme.semanticPalette.success,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _saveSuccess!,
                      style: TextStyle(
                        color: theme.semanticPalette.success,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // ── Security section ──
            Text(
              t.t('profile.security'),
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),

            // 2FA setup
            Semantics(
              button: true,
              label: 'Configurer l’authentification à deux facteurs',
              child: Card(
                child: ListTile(
                  leading:
                      Icon(Icons.security, color: theme.colorScheme.primary),
                  title: Text(t.t('twoFactor.title')),
                  subtitle: Text(t.t('profile.twoFactorSubtitle')),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/profile/2fa'),
                ),
              ),
            ),

            // Biometric toggle
            if (authState.biometricAvailable) ...[
              Card(
                child: SwitchListTile(
                  secondary:
                      Icon(Icons.fingerprint, color: theme.colorScheme.primary),
                  title: Text(t.t('profile.biometricTitle')),
                  subtitle: Text(t.t('profile.biometricSubtitle')),
                  value: authState.biometricEnabled,
                  onChanged: (value) {
                    ref.read(authProvider.notifier).setBiometricEnabled(value);
                  },
                ),
              ),
            ],

            // Change password
            Card(
              child: ListTile(
                leading:
                    Icon(Icons.lock_outline, color: theme.colorScheme.primary),
                title: Text(t.t('profile.changePassword')),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.push('/profile/password'),
              ),
            ),
            Card(
              child: ListTile(
                leading: Icon(
                  Icons.privacy_tip_outlined,
                  color: theme.colorScheme.primary,
                ),
                title: Text(t.t('settings.privacy')),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.push('/settings/privacy'),
              ),
            ),
            const SizedBox(height: 24),

            Text(
              t.t('profile.preferences'),
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    DropdownButtonFormField<ThemeMode>(
                      key: const Key('profile.theme.mode'),
                      initialValue: themeMode,
                      decoration: InputDecoration(
                        labelText: t.t('profile.theme'),
                        border: const OutlineInputBorder(),
                      ),
                      items: ThemeMode.values
                          .map(
                            (mode) => DropdownMenuItem<ThemeMode>(
                              value: mode,
                              child: Text(_themeModeLabels[mode] ?? mode.name),
                            ),
                          )
                          .toList(),
                      onChanged: (value) {
                        if (value != null) {
                          ref
                              .read(themeModeProvider.notifier)
                              .setThemeMode(value);
                        }
                      },
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      key: const Key('profile.locale.code'),
                      initialValue: localeCode,
                      decoration: InputDecoration(
                        labelText: t.t('profile.language'),
                        border: const OutlineInputBorder(),
                      ),
                      items: _localeLabels.entries
                          .map(
                            (entry) => DropdownMenuItem<String>(
                              value: entry.key,
                              child: Text(entry.value),
                            ),
                          )
                          .toList(),
                      onChanged: (value) {
                        if (value != null) {
                          ref.read(localeProvider.notifier).setLocale(value);
                        }
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Logout button
            Semantics(
              button: true,
              label: 'Se déconnecter',
              child: OutlinedButton.icon(
                onPressed: () => ref.read(authProvider.notifier).logout(),
                icon: Icon(Icons.logout, color: theme.colorScheme.error),
                label: Text(
                  t.t('profile.logout'),
                  style: TextStyle(color: theme.colorScheme.error),
                ),
                style: OutlinedButton.styleFrom(
                  side: BorderSide(color: theme.colorScheme.error),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRoleProfileSection(ThemeData theme, String role) {
    final t = AppLocalizations.of(ref);

    if (_profileLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 16),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (_profileError != null && _profileData == null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Column(
          children: [
            Text(
              _profileError!,
              style: TextStyle(color: theme.colorScheme.error),
            ),
            TextButton(
              onPressed: _fetchProfile,
              child: Text(AppLocalizations.of(ref).t('common.retry')),
            ),
          ],
        ),
      );
    }

    final student = _profileData?['student_profile'] as Map<String, dynamic>?;
    final parent = _profileData?['parent_profile'] as Map<String, dynamic>?;
    final teacher = _profileData?['teacher_profile'] as Map<String, dynamic>?;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              _profileSectionTitle(role),
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            if (!_editing)
              TextButton.icon(
                onPressed: () => setState(() => _editing = true),
                icon: const Icon(Icons.edit, size: 16),
                label: Text(t.t('common.edit')),
              )
            else
              Row(
                children: [
                  TextButton(
                    onPressed: _saving
                        ? null
                        : () {
                            _populateEditFields(_profileData ?? {});
                            setState(() => _editing = false);
                          },
                    child: Text(t.t('common.cancel')),
                  ),
                  const SizedBox(width: 4),
                  FilledButton(
                    onPressed: _saving ? null : _saveProfile,
                    child: _saving
                        ? SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: theme.colorScheme.onPrimary,
                            ),
                          )
                        : Text(t.t('common.save')),
                  ),
                ],
              ),
          ],
        ),
        const SizedBox(height: 8),
        if (_editing)
          _buildEditForm(role)
        else
          _buildViewForm(role, student, parent, teacher),
        const SizedBox(height: 24),
      ],
    );
  }

  String _profileSectionTitle(String role) {
    switch (role) {
      case 'STD':
        return 'Informations élève';
      case 'PAR':
        return 'Informations parent';
      case 'TCH':
        return 'Informations enseignant';
      default:
        return 'Profil';
    }
  }

  // ── View mode ──
  Widget _buildViewForm(
    String role,
    Map<String, dynamic>? student,
    Map<String, dynamic>? parent,
    Map<String, dynamic>? teacher,
  ) {
    final hasData = (student != null || parent != null || teacher != null);
    if (!hasData) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'Aucun détail de profil. Cliquez sur Modifier pour ajouter.',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
              fontSize: 13,
            ),
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            if (role == 'STD' && student != null) ...[
              if (student['student_number'] != null)
                _profileRow('N° élève', student['student_number']),
              if (student['date_of_birth'] != null)
                _profileRow('Date de naissance', student['date_of_birth']),
              if (student['class_level'] != null)
                _profileRow('Niveau', student['class_level']),
            ],
            if (role == 'PAR' && parent != null) ...[
              if (parent['relationship_type'] != null)
                _profileRow(
                  'Lien de parenté',
                  _relationshipLabels[parent['relationship_type']] ??
                      parent['relationship_type'],
                ),
              if (parent['cin_number'] != null)
                _profileRow('CIN', parent['cin_number']),
              if (parent['emergency_phone'] != null)
                _profileRow('Tél. urgence', parent['emergency_phone']),
            ],
            if (role == 'TCH' && teacher != null) ...[
              if (teacher['employee_id'] != null)
                _profileRow('N° employé', teacher['employee_id']),
              if (teacher['subject_specialty'] != null)
                _profileRow('Spécialité', teacher['subject_specialty']),
              if (teacher['qualification'] != null)
                _profileRow('Qualification', teacher['qualification']),
              // Phase 10C: Reward points
              _profileRow(
                'Points de récompense',
                '${teacher['reward_points'] ?? 0}',
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _profileRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: TextStyle(
                fontSize: 13,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 14)),
          ),
        ],
      ),
    );
  }

  // ── Edit mode ──
  Widget _buildEditForm(String role) {
    final t = AppLocalizations.of(ref);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            if (role == 'STD') ...[
              TextFormField(
                controller: _dobController,
                readOnly: true,
                decoration: InputDecoration(
                  labelText: t.t('profileForm.birthDate'),
                  prefixIcon: const Icon(Icons.calendar_today),
                  border: const OutlineInputBorder(),
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
              DropdownButtonFormField<String>(
                initialValue: _classLevel.isEmpty ? null : _classLevel,
                decoration: InputDecoration(
                  labelText: t.t('profileForm.gradeLevel'),
                  prefixIcon: const Icon(Icons.school_outlined),
                  border: const OutlineInputBorder(),
                ),
                items: [
                  DropdownMenuItem(
                    value: '',
                    child: Text(t.t('profileForm.select')),
                  ),
                  ...Taxonomy.levelBands.map(
                    (level) => DropdownMenuItem(
                      value: level,
                      child: Text(level),
                    ),
                  ),
                ],
                onChanged: (value) => setState(() => _classLevel = value ?? ''),
              ),
            ],
            if (role == 'PAR') ...[
              DropdownButtonFormField<String>(
                initialValue:
                    _relationshipType.isEmpty ? null : _relationshipType,
                decoration: InputDecoration(
                  labelText: t.t('profileForm.relationship'),
                  prefixIcon: const Icon(Icons.family_restroom),
                  border: const OutlineInputBorder(),
                ),
                items: [
                  DropdownMenuItem(
                    value: '',
                    child: Text(t.t('profileForm.select')),
                  ),
                  ..._relationshipTypes.map(
                    (rt) => DropdownMenuItem(
                      value: rt,
                      child: Text(_relationshipLabels[rt] ?? rt),
                    ),
                  ),
                ],
                onChanged: (v) => setState(() => _relationshipType = v ?? ''),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _cinController,
                decoration: InputDecoration(
                  labelText: t.t('profileForm.cin'),
                  prefixIcon: const Icon(Icons.badge_outlined),
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _emergencyPhoneController,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(
                  labelText: t.t('profileForm.emergencyPhone'),
                  prefixIcon: const Icon(Icons.phone_outlined),
                  border: const OutlineInputBorder(),
                ),
              ),
            ],
            if (role == 'TCH') ...[
              DropdownButtonFormField<String>(
                initialValue:
                    _subjectSpecialty.isEmpty ? null : _subjectSpecialty,
                decoration: InputDecoration(
                  labelText: t.t('profileForm.specialty'),
                  prefixIcon: const Icon(Icons.book_outlined),
                  border: const OutlineInputBorder(),
                ),
                items: [
                  DropdownMenuItem(
                    value: '',
                    child: Text(t.t('profileForm.select')),
                  ),
                  ...Taxonomy.subjects.map(
                    (subject) => DropdownMenuItem(
                      value: subject,
                      child: Text(_subjectLabel(subject, t.locale)),
                    ),
                  ),
                ],
                onChanged: (value) =>
                    setState(() => _subjectSpecialty = value ?? ''),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _qualificationController,
                decoration: InputDecoration(
                  labelText: t.t('profileForm.qualification'),
                  prefixIcon: const Icon(Icons.workspace_premium_outlined),
                  border: const OutlineInputBorder(),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _subjectLabel(String code, String locale) {
    final titles = Taxonomy.subjectTitles[code];
    return titles?[locale] ?? titles?['fr'] ?? code;
  }
}

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoTile({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListTile(
      leading: Icon(icon, color: theme.colorScheme.primary),
      title: Text(
        label,
        style: theme.textTheme.bodySmall?.copyWith(
          color: theme.colorScheme.onSurfaceVariant,
        ),
      ),
      subtitle: Text(value, style: theme.textTheme.bodyLarge),
    );
  }
}
