part of 'register_screen.dart';

extension _RegisterSteps on _RegisterScreenState {
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
          onChanged: (_) => _applyState(() {}),
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
          onChanged: (_) => _applyState(() {}),
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
          decoration: const InputDecoration(
            labelText: 'Confirmer le mot de passe',
            prefixIcon: Icon(Icons.lock_outlined),
            border: OutlineInputBorder(),
          ),
          onChanged: (_) => _applyState(() {}),
        ),
        if (confirm.isNotEmpty && password != confirm) ...[
          const SizedBox(height: 4),
          Padding(
            padding: EdgeInsets.only(left: 8),
            child: Text(
              'Les mots de passe ne correspondent pas',
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
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _relationshipType.isEmpty ? null : _relationshipType,
          decoration: const InputDecoration(
            labelText: 'Lien de parenté',
            prefixIcon: Icon(Icons.family_restroom),
            border: OutlineInputBorder(),
          ),
          items: [
            const DropdownMenuItem(
              value: '',
              child: Text('Sélectionner (optionnel)'),
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
                    ? SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: theme.colorScheme.onPrimary,
                        ),
                      )
                    : const Text(
                        'Créer le compte',
                        style: TextStyle(fontSize: 16),
                      ),
              ),
            ),
          ],
        ),
      ],
    );
  }

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
              : const Text('Vérifier', style: TextStyle(fontSize: 16)),
        ),
        const SizedBox(height: 8),
        Center(
          child: TextButton(
            onPressed: _navigateToHome,
            child: Text(
              'Passer pour l\'instant',
              style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
            ),
          ),
        ),
      ],
    );
  }
}
