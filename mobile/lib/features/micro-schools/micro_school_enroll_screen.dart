import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';

import 'micro_schools_provider.dart';

class MicroSchoolEnrollScreen extends ConsumerStatefulWidget {
  final String schoolId;

  const MicroSchoolEnrollScreen({
    super.key,
    required this.schoolId,
  });

  @override
  ConsumerState<MicroSchoolEnrollScreen> createState() =>
      _MicroSchoolEnrollScreenState();
}

class _MicroSchoolEnrollScreenState
    extends ConsumerState<MicroSchoolEnrollScreen> {
  final _formKey = GlobalKey<FormState>();
  final _studentNameController = TextEditingController();

  @override
  void dispose() {
    _studentNameController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    await ref.read(microSchoolActionProvider.notifier).enroll(
          schoolId: widget.schoolId,
          studentName: _studentNameController.text.trim(),
        );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Enrollment submitted')),
    );
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final actionState = ref.watch(microSchoolActionProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('microSchools.enroll'))),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _studentNameController,
                decoration: InputDecoration(
                  labelText: t.t('microSchools.studentName'),
                  border: const OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Student name is required';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: actionState.isLoading ? null : _submit,
                  icon: actionState.isLoading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.person_add_alt_1),
                  label: Text(t.t('microSchools.enroll')),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
