import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'question_bank_provider.dart';

class QuestionBankImportScreen extends ConsumerStatefulWidget {
  const QuestionBankImportScreen({super.key});

  @override
  ConsumerState<QuestionBankImportScreen> createState() =>
      _QuestionBankImportScreenState();
}

class _QuestionBankImportScreenState
    extends ConsumerState<QuestionBankImportScreen> {
  final _quizIdController = TextEditingController();
  bool _loading = false;
  int? _imported;
  int? _skipped;

  @override
  void dispose() {
    _quizIdController.dispose();
    super.dispose();
  }

  Future<void> _import() async {
    setState(() => _loading = true);
    try {
      final result = await ref
          .read(questionBankRepositoryProvider)
          .importFromQuiz(_quizIdController.text.trim());
      ref.invalidate(questionBankQuestionsProvider);
      ref.invalidate(questionBankStatsProvider);
      setState(() {
        _imported = result.imported;
        _skipped = result.skipped;
      });
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
      appBar: AppBar(title: Text(t.t('questionBank.import'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _quizIdController,
            decoration: const InputDecoration(
              labelText: 'Quiz ID',
              helperText: 'Imports questions from an existing quiz',
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: _loading ? null : _import,
              icon: _loading
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.upload_file_outlined),
              label: Text(t.t('questionBank.import')),
            ),
          ),
          if (_imported != null && _skipped != null) ...[
            const SizedBox(height: 24),
            AppDataTable(
              columns: const [
                AppColumn<List<String>>(
                  header: 'Imported',
                  cellBuilder: _importedCell,
                ),
                AppColumn<List<String>>(
                  header: 'Skipped',
                  cellBuilder: _skippedCell,
                ),
              ],
              rows: [
                ['$_imported', '$_skipped'],
              ],
            ),
          ],
        ],
      ),
    );
  }
}

Widget _importedCell(List<String> row) => Text(row[0]);

Widget _skippedCell(List<String> row) => Text(row[1]);
