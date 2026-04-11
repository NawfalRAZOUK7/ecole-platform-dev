import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/question_bank.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class GenerateQuizScreen extends ConsumerStatefulWidget {
  const GenerateQuizScreen({super.key});

  @override
  ConsumerState<GenerateQuizScreen> createState() => _GenerateQuizScreenState();
}

class _GenerateQuizScreenState extends ConsumerState<GenerateQuizScreen> {
  final _subjectController = TextEditingController();
  final _countController = TextEditingController(text: '5');
  final _tagsController = TextEditingController();
  bool _loading = false;
  String difficulty = 'medium';
  GeneratedQuestionQuiz? _result;

  @override
  void dispose() {
    _subjectController.dispose();
    _countController.dispose();
    _tagsController.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    setState(() => _loading = true);
    try {
      final result =
          await ref.read(questionBankRepositoryProvider).generateQuiz(
                subject: _subjectController.text.trim(),
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
          TextField(
            controller: _subjectController,
            decoration: const InputDecoration(labelText: 'Subject'),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: difficulty,
            decoration: const InputDecoration(labelText: 'Difficulty'),
            items: const [
              DropdownMenuItem(value: 'easy', child: Text('Easy')),
              DropdownMenuItem(value: 'medium', child: Text('Medium')),
              DropdownMenuItem(value: 'hard', child: Text('Hard')),
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
            decoration: const InputDecoration(labelText: 'Question count'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _tagsController,
            decoration: const InputDecoration(
              labelText: 'Tags (comma separated)',
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
}
