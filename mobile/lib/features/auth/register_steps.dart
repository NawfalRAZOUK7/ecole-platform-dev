part of 'register_screen.dart';

extension _RegisterSteps on _RegisterScreenState {
  Widget _buildCodeStep(ThemeData theme) {
    final t = AppLocalizations.of(ref);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          t.t('register.codePrompt'),
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
          decoration: InputDecoration(
            labelText: t.t('register.codeLabel'),
            prefixIcon: const Icon(Icons.confirmation_number_outlined),
            border: const OutlineInputBorder(),
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
          child: Text(
            t.t('register.next'),
            style: const TextStyle(fontSize: 16),
          ),
        ),
        const SizedBox(height: 16),
        Center(
          child: TextButton(
            onPressed: () => context.go('/login'),
            child: Text(t.t('register.haveAccount')),
          ),
        ),
      ],
    );
  }

  Widget _buildInfoStep(ThemeData theme) {
    final password = _passwordController.text;
    final confirm = _confirmPasswordController.text;
    final canProceed = _emailController.text.isNotEmpty &&
        _fullNameController.text.isNotEmpty &&
        password.isNotEmpty &&
        _allRulesPassed(password) &&
        password == confirm;

    final t = AppLocalizations.of(ref);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          t.t('register.infoPrompt'),
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
          decoration: InputDecoration(
            labelText: t.t('auth.email'),
            prefixIcon: const Icon(Icons.email_outlined),
            border: const OutlineInputBorder(),
          ),
          onChanged: (_) => _applyState(() {}),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _fullNameController,
          textCapitalization: TextCapitalization.words,
          decoration: InputDecoration(
            labelText: t.t('register.fullName'),
            prefixIcon: const Icon(Icons.person_outlined),
            border: const OutlineInputBorder(),
          ),
          onChanged: (_) => _applyState(() {}),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _phoneController,
          keyboardType: TextInputType.phone,
          decoration: InputDecoration(
            labelText: t.t('register.phoneOptional'),
            prefixIcon: const Icon(Icons.phone_outlined),
            border: const OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _passwordController,
          obscureText: true,
          autofillHints: const [AutofillHints.newPassword],
          decoration: InputDecoration(
            labelText: t.t('auth.password'),
            prefixIcon: const Icon(Icons.lock_outlined),
            border: const OutlineInputBorder(),
          ),
          onChanged: (_) => _applyState(() {}),
        ),
        if (password.isNotEmpty) ...[
          const SizedBox(height: 8),
          ..._passwordRules.entries.map((entry) {
            final passed = _checkRule(entry.key, password);
            final color = passed
                ? theme.semanticPalette.success
                : theme.colorScheme.error;
            return Padding(
              padding: const EdgeInsets.only(left: 8, bottom: 2),
              child: Row(
                children: [
                  Icon(
                    passed ? Icons.check_circle : Icons.cancel,
                    size: 14,
                    color: color,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    entry.value,
                    style: TextStyle(
                      fontSize: 12,
                      color: color,
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
        const SizedBox(height: 12),
        TextFormField(
          controller: _confirmPasswordController,
          obscureText: true,
          decoration: InputDecoration(
            labelText: t.t('auth.confirmPassword'),
            prefixIcon: const Icon(Icons.lock_outlined),
            border: const OutlineInputBorder(),
          ),
          onChanged: (_) => _applyState(() {}),
        ),
        if (confirm.isNotEmpty && password != confirm) ...[
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.only(left: 8),
            child: Text(
              t.t('register.passwordMismatch'),
              style: TextStyle(fontSize: 12, color: theme.colorScheme.error),
            ),
          ),
        ],
        const SizedBox(height: 20),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () => _applyState(() => _step = _Step.code),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: Text(t.t('register.back')),
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
                child: Text(
                  t.t('register.next'),
                  style: const TextStyle(fontSize: 16),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildRoleStep(ThemeData theme) {
    final t = AppLocalizations.of(ref);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          t.t('register.rolePrompt'),
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 20),
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
              child: Text(t.t('profileForm.selectOptional')),
            ),
            ...Taxonomy.levelBands.map(
              (level) => DropdownMenuItem(
                value: level,
                child: Text(level),
              ),
            ),
          ],
          onChanged: (value) => _applyState(() => _classLevel = value ?? ''),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _relationshipType.isEmpty ? null : _relationshipType,
          decoration: InputDecoration(
            labelText: t.t('profileForm.relationship'),
            prefixIcon: const Icon(Icons.family_restroom),
            border: const OutlineInputBorder(),
          ),
          items: [
            DropdownMenuItem(
              value: '',
              child: Text(t.t('profileForm.selectOptional')),
            ),
            ..._relationshipTypes.map(
              (relationship) => DropdownMenuItem(
                value: relationship,
                child: Text(_relationshipLabels[relationship] ?? relationship),
              ),
            ),
          ],
          onChanged: (value) =>
              _applyState(() => _relationshipType = value ?? ''),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _subjectSpecialty.isEmpty ? null : _subjectSpecialty,
          decoration: InputDecoration(
            labelText: t.t('profileForm.specialty'),
            prefixIcon: const Icon(Icons.book_outlined),
            border: const OutlineInputBorder(),
          ),
          items: [
            DropdownMenuItem(
              value: '',
              child: Text(t.t('profileForm.selectOptional')),
            ),
            ...Taxonomy.subjects.map(
              (subject) => DropdownMenuItem(
                value: subject,
                child: Text(_subjectLabel(subject, t.locale)),
              ),
            ),
          ],
          onChanged: (value) =>
              _applyState(() => _subjectSpecialty = value ?? ''),
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
        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: _loading
                    ? null
                    : () => _applyState(() => _step = _Step.info),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: Text(t.t('register.back')),
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
                    ? SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: theme.colorScheme.onPrimary,
                        ),
                      )
                    : Text(
                        t.t('register.createAccount'),
                        style: const TextStyle(fontSize: 16),
                      ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildOtpStep(ThemeData theme) {
    final t = AppLocalizations.of(ref);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          t.t('register.otpPrompt'),
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
          decoration: InputDecoration(
            labelText: t.t('auth.verificationCode'),
            prefixIcon: const Icon(Icons.pin_outlined),
            border: const OutlineInputBorder(),
            counterText: '',
          ),
          enabled: !_loading,
          onChanged: (_) => _applyState(() {}),
        ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: _loading || _otpController.text.length != 6
              ? null
              : _handleOtpSubmit,
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: _loading
              ? SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: theme.colorScheme.onPrimary,
                  ),
                )
              : Text(
                  t.t('common.verify'),
                  style: const TextStyle(fontSize: 16),
                ),
        ),
        const SizedBox(height: 8),
        Center(
          child: TextButton(
            onPressed: _navigateToHome,
            child: Text(
              t.t('register.skipForNow'),
              style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
            ),
          ),
        ),
      ],
    );
  }

  String _subjectLabel(String code, String locale) {
    final titles = Taxonomy.subjectTitles[code];
    return titles?[locale] ?? titles?['fr'] ?? code;
  }
}
