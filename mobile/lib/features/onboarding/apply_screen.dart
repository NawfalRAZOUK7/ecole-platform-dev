/// ApplyScreen — public onboarding application (no auth).
///
/// A prospective formal school or micro-école/educator submits a request to the
/// public endpoints (`/applications/{formal-school,micro-school}`, skipAuth). A
/// SuperAdmin reviews it on the web platform console; on approval the applicant
/// gets an invitation code by email to complete registration.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class ApplyScreen extends ConsumerStatefulWidget {
  const ApplyScreen({super.key});

  @override
  ConsumerState<ApplyScreen> createState() => _ApplyScreenState();
}

class _ApplyScreenState extends ConsumerState<ApplyScreen> {
  String _type = 'formal_school'; // or 'micro_school'
  bool _submitting = false;
  bool _sent = false;
  String? _error;

  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _city = TextEditingController();
  final _orgName = TextEditingController();
  final _address = TextEditingController();
  final _extra =
      TextEditingController(); // level (formal) / neighborhood (micro)
  final _capacity = TextEditingController();
  final _notes = TextEditingController();

  @override
  void dispose() {
    for (final c in [
      _name,
      _email,
      _phone,
      _city,
      _orgName,
      _address,
      _extra,
      _capacity,
      _notes,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    if (_name.text.trim().isEmpty ||
        _email.text.trim().isEmpty ||
        _orgName.text.trim().isEmpty) {
      setState(() => _error = 'Champs requis manquants');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    final isFormal = _type == 'formal_school';
    final path =
        isFormal ? '/applications/formal-school' : '/applications/micro-school';
    final body = <String, dynamic>{
      'applicant_name': _name.text.trim(),
      'applicant_email': _email.text.trim(),
      if (_phone.text.trim().isNotEmpty) 'applicant_phone': _phone.text.trim(),
      if (_city.text.trim().isNotEmpty) 'city': _city.text.trim(),
      'org_name': _orgName.text.trim(),
      if (_address.text.trim().isNotEmpty) 'address': _address.text.trim(),
      if (_notes.text.trim().isNotEmpty) 'notes': _notes.text.trim(),
    };
    if (isFormal) {
      if (_extra.text.trim().isNotEmpty) {
        body['level_band'] = _extra.text.trim();
      }
    } else {
      if (_extra.text.trim().isNotEmpty) {
        body['neighborhood'] = _extra.text.trim();
      }
      final cap = int.tryParse(_capacity.text.trim());
      if (cap != null) body['max_capacity'] = cap;
    }
    try {
      await ref.read(apiClientProvider).post(path, body: body, skipAuth: true);
      if (mounted) setState(() => _sent = true);
    } catch (e) {
      if (mounted) setState(() => _error = 'Erreur: $e');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final locale = ref.watch(localeProvider);
    String tr(String fr, String en, String ar) =>
        locale == 'ar' ? ar : (locale == 'en' ? en : fr);

    if (_sent) {
      return Scaffold(
        appBar: AppBar(
          title: Text(tr('Demande envoyée', 'Request sent', 'تم الإرسال')),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('✅', style: TextStyle(fontSize: 56)),
                const SizedBox(height: 12),
                Text(
                  tr(
                    'Votre demande a été reçue. Une fois approuvée, vous recevrez par email un lien d\'activation pour définir votre mot de passe.',
                    'Your request was received. Once approved, you will receive an email with an activation link to set your password.',
                    'تم استلام طلبك. بعد الموافقة، ستصلك رسالة بريد إلكتروني تتضمّن رابط تفعيل لتعيين كلمة المرور.',
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(tr('Retour', 'Back', 'رجوع')),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final isFormal = _type == 'formal_school';
    return Scaffold(
      appBar: AppBar(
        title: Text(tr("Demande d'inscription", 'Apply', 'طلب التسجيل')),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Wrap(
            spacing: 8,
            children: [
              ChoiceChip(
                label:
                    Text(tr('École formelle', 'Formal school', 'مدرسة نظامية')),
                selected: isFormal,
                onSelected: (_) => setState(() => _type = 'formal_school'),
              ),
              ChoiceChip(
                label: Text(tr('Micro-école', 'Micro-school', 'مدرسة مصغّرة')),
                selected: !isFormal,
                onSelected: (_) => setState(() => _type = 'micro_school'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _field(_name, tr('Votre nom *', 'Your name *', 'اسمك *')),
          _field(
            _email,
            tr('Email *', 'Email *', 'البريد *'),
            keyboard: TextInputType.emailAddress,
          ),
          _field(
            _phone,
            tr('Téléphone', 'Phone', 'الهاتف'),
            keyboard: TextInputType.phone,
          ),
          _field(_city, tr('Ville', 'City', 'المدينة')),
          _field(
            _orgName,
            isFormal
                ? tr("Nom de l'école *", 'School name *', 'اسم المدرسة *')
                : tr(
                    'Nom de la micro-école *',
                    'Micro-school name *',
                    'اسم المدرسة المصغّرة *',
                  ),
          ),
          _field(_address, tr('Adresse', 'Address', 'العنوان')),
          _field(
            _extra,
            isFormal
                ? tr('Niveau', 'Level', 'المستوى')
                : tr('Quartier', 'Neighborhood', 'الحي'),
          ),
          if (!isFormal)
            _field(
              _capacity,
              tr('Capacité', 'Capacity', 'السعة'),
              keyboard: TextInputType.number,
            ),
          _field(_notes, tr('Message', 'Message', 'رسالة'), maxLines: 3),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _submitting ? null : _submit,
            child: Text(
              _submitting
                  ? tr('Envoi…', 'Sending…', 'جارٍ الإرسال…')
                  : tr('Envoyer la demande', 'Send request', 'إرسال الطلب'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _field(
    TextEditingController controller,
    String label, {
    TextInputType? keyboard,
    int maxLines = 1,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        keyboardType: keyboard,
        maxLines: maxLines,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
      ),
    );
  }
}
