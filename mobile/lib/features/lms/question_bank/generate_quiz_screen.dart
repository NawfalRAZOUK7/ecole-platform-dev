import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/lms/question_bank.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/taxonomy/taxonomy.g.dart';

class GenerateQuizScreen extends ConsumerStatefulWidget {
  const GenerateQuizScreen({super.key});

  @override
  ConsumerState<GenerateQuizScreen> createState() => _GenerateQuizScreenState();
}

class _GenerateQuizScreenState extends ConsumerState<GenerateQuizScreen> {
  final _countController = TextEditingController(text: '5');
  final _tagsController = TextEditingController();
  bool _loading = false;
  String _subject = Taxonomy.subjects.first;
  String difficulty = 'medium';
  GeneratedQuestionQuiz? _result;

  @override
  void dispose() {
    _countController.dispose();
    _tagsController.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    setState(() => _loading = true);
    try {
      final result =
          await ref.read(questionBankRepositoryProvider).generateQuiz(
                subject: _subject,
                difficulty: difficulty,
                count: int.tryParse(_countController.text) ?? 5,
                tags: _tagsController.text
                    .split(',')
                    .map((item) => item.trim())
                    .where((item) => item.isNotEmpty)
                    .toList(),
              );
      setState(() => _result = result);
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('questionBank.generate'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DropdownButtonFormField<String>(
            initialValue: _subject,
            menuMaxHeight: 320,
            decoration: InputDecoration(labelText: t.t('questionBank.subject')),
            items: Taxonomy.subjects
                .map(
                  (subject) => DropdownMenuItem(
                    value: subject,
                    child: Text(_subjectLabel(subject, t.locale)),
                  ),
                )
                .toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() => _subject = value);
              }
            },
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: difficulty,
            decoration:
                InputDecoration(labelText: t.t('questionBank.difficulty')),
            items: [
              DropdownMenuItem(
                value: 'easy',
                child: Text(t.t('quiz.easy')),
              ),
              DropdownMenuItem(
                value: 'medium',
                child: Text(t.t('quiz.medium')),
              ),
              DropdownMenuItem(
                value: 'hard',
                child: Text(t.t('quiz.hard')),
              ),
            ],
            onChanged: (value) {
              if (value != null) {
                setState(() => difficulty = value);
              }
            },
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _countController,
            keyboardType: TextInputType.number,
            decoration:
                InputDecoration(labelText: t.t('questionBank.questionCount')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _tagsController,
            decoration: InputDecoration(
              labelText: t.t('questionBank.tags'),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: _loading ? null : _generate,
              icon: _loading
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.auto_awesome_outlined),
              label: Text(t.t('questionBank.generate')),
            ),
          ),
          if (_result != null) ...[
            const SizedBox(height: 24),
            Text(
              'Generated ${_result!.total} question(s)',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 12),
            ..._result!.questions.map(
              (question) => Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  title: Text(question.text),
                  subtitle:
                      Text('${question.subject} · ${question.difficulty}'),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _subjectLabel(String code, String locale) {
    final titles = Taxonomy.subjectTitles[code];
    return titles?[locale] ?? titles?['fr'] ?? code;
  }
}
