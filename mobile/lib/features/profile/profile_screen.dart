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
  final _classLevelController = TextEditingController();
  String _relationshipType = '';
  final _cinController = TextEditingController();
  final _emergencyPhoneController = TextEditingController();
  final _subjectController = TextEditingController();
  final _qualificationController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchProfile();
  }

  @override
  void dispose() {
    _dobController.dispose();
    _classLevelController.dispose();
    _cinController.dispose();
    _emergencyPhoneController.dispose();
    _subjectController.dispose();
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
    _classLevelController.text = student?['class_level'] as String? ?? '';
    _relationshipType = parent?['relationship_type'] as String? ?? '';
    _cinController.text = parent?['cin_number'] as String? ?? '';
    _emergencyPhoneController.text =
        parent?['emergency_phone'] as String? ?? '';
    _subjectController.text = teacher?['subject_specialty'] as String? ?? '';
    _qualificationController.text =
        teacher?['qualification'] as String? ?? '';
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
    if (_classLevelController.text.isNotEmpty) {
      body['class_level'] = _classLevelController.text;
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
    if (_subjectController.text.isNotEmpty) {
      body['subject_specialty'] = _subjectController.text;
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

    if (user == null) return const SizedBox.shrink();

    return Scaffold(
      appBar: AppBar(title: const Text('Mon Profil')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // Avatar
          Center(
            child: CircleAvatar(
              radius: 48,
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Text(
                user.fullName.isNotEmpty ? user.fullName[0].toUpperCase() : '?',
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.primary,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Center(
            child: Text(
              user.fullName,
              style: theme.textTheme.headlineSmall
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
          ),
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: theme.colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                _roleLabels[user.role] ?? user.role,
                style: TextStyle(
                  color: theme.colorScheme.primary,
                  fontWeight: FontWeight.w600,
                ),
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

          // Permissions
          if (user.permissions.isNotEmpty) ...[
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
                  .map((p) => Chip(
                        label: Text(p, style: const TextStyle(fontSize: 10)),
                        padding: EdgeInsets.zero,
                        visualDensity: VisualDensity.compact,
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ))
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
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, color: Colors.green, size: 20),
                  const SizedBox(width: 8),
                  Text(_saveSuccess!,
                      style: const TextStyle(color: Colors.green, fontSize: 13)),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // ── Security section ──
          Text(
            'Sécurité',
            style: theme.textTheme.titleSmall
                ?.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),

          // 2FA setup
          Card(
            child: ListTile(
              leading: Icon(Icons.security, color: theme.colorScheme.primary),
              title: const Text('Authentification 2FA'),
              subtitle: const Text('Configurer la double authentification'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/profile/2fa'),
            ),
          ),

          // Biometric toggle
          if (authState.biometricAvailable) ...[
            Card(
              child: SwitchListTile(
                secondary:
                    Icon(Icons.fingerprint, color: theme.colorScheme.primary),
                title: const Text('Déverrouillage biométrique'),
                subtitle: const Text('Empreinte digitale / Face ID'),
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
              leading: Icon(Icons.lock_outline, color: theme.colorScheme.primary),
              title: const Text('Changer le mot de passe'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/profile/password'),
            ),
          ),
          const SizedBox(height: 24),

          // Logout button
          OutlinedButton.icon(
            onPressed: () => ref.read(authProvider.notifier).logout(),
            icon: const Icon(Icons.logout, color: Colors.red),
            label: const Text('Déconnexion',
                style: TextStyle(color: Colors.red)),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: Colors.red),
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRoleProfileSection(ThemeData theme, String role) {
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
            Text(_profileError!, style: TextStyle(color: theme.colorScheme.error)),
            TextButton(onPressed: _fetchProfile, child: const Text('Réessayer')),
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
                label: const Text('Modifier'),
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
                    child: const Text('Annuler'),
                  ),
                  const SizedBox(width: 4),
                  FilledButton(
                    onPressed: _saving ? null : _saveProfile,
                    child: _saving
                        ? const SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Enregistrer'),
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
            style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
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
                _profileRow('Lien de parenté',
                    _relationshipLabels[parent['relationship_type']] ?? parent['relationship_type']),
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
            child: Text(label,
                style: const TextStyle(
                    fontSize: 13, color: Colors.grey, fontWeight: FontWeight.w500)),
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
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            if (role == 'STD') ...[
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
              TextFormField(
                controller: _classLevelController,
                decoration: const InputDecoration(
                  labelText: 'Niveau scolaire',
                  prefixIcon: Icon(Icons.school_outlined),
                  border: OutlineInputBorder(),
                ),
              ),
            ],
            if (role == 'PAR') ...[
              DropdownButtonFormField<String>(
                value: _relationshipType.isEmpty ? null : _relationshipType,
                decoration: const InputDecoration(
                  labelText: 'Lien de parenté',
                  prefixIcon: Icon(Icons.family_restroom),
                  border: OutlineInputBorder(),
                ),
                items: [
                  const DropdownMenuItem(
                      value: '', child: Text('Sélectionner')),
                  ..._relationshipTypes.map((rt) => DropdownMenuItem(
                        value: rt,
                        child: Text(_relationshipLabels[rt] ?? rt),
                      )),
                ],
                onChanged: (v) =>
                    setState(() => _relationshipType = v ?? ''),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _cinController,
                decoration: const InputDecoration(
                  labelText: 'CIN (Carte nationale)',
                  prefixIcon: Icon(Icons.badge_outlined),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _emergencyPhoneController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Téléphone d\'urgence',
                  prefixIcon: Icon(Icons.phone_outlined),
                  border: OutlineInputBorder(),
                ),
              ),
            ],
            if (role == 'TCH') ...[
              TextFormField(
                controller: _subjectController,
                decoration: const InputDecoration(
                  labelText: 'Spécialité',
                  prefixIcon: Icon(Icons.book_outlined),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _qualificationController,
                decoration: const InputDecoration(
                  labelText: 'Diplôme / Qualification',
                  prefixIcon: Icon(Icons.workspace_premium_outlined),
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ],
        ),
      ),
    );
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
      title: Text(label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          )),
      subtitle: Text(value, style: theme.textTheme.bodyLarge),
    );
  }
}
