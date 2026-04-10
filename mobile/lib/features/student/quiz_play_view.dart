part of 'quiz_player_screen.dart';

extension _QuizPlayView on _QuizPlayerScreenState {
  Widget _buildPlayView(BuildContext context) {
    final theme = Theme.of(context);
    final question = _questions[_currentIdx];
    final totalQuestions = _questions.length;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          tooltip: 'Quit quiz',
          icon: const Icon(Icons.close),
          onPressed: () => _showExitConfirm(context),
        ),
        title: Text('${_currentIdx + 1}/$totalQuestions'),
        actions: [
          if (_secondsLeft > 0) _QuizTimerChip(secondsLeft: _secondsLeft),
        ],
      ),
      body: Column(
        children: [
          _ProgressDots(
            total: totalQuestions,
            current: _currentIdx,
            answered: _answers,
            questions: _questions,
            onTap: _goToQuestion,
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${question.points} pt${question.points > 1 ? 's' : ''}',
                      style: TextStyle(
                        fontSize: 12,
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    question.questionText,
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 24),
                  _buildQuestionInput(question),
                ],
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              border: Border(
                top: BorderSide(color: theme.colorScheme.outline.withAlpha(50)),
              ),
            ),
            child: Row(
              children: [
                if (_currentIdx > 0)
                  OutlinedButton.icon(
                    onPressed: () => _goToQuestion(_currentIdx - 1),
                    icon: const Icon(Icons.arrow_back, size: 18),
                    label: const Text('Précédent'),
                  )
                else
                  const SizedBox.shrink(),
                const Spacer(),
                if (_currentIdx < totalQuestions - 1)
                  FilledButton.icon(
                    onPressed: () => _goToQuestion(_currentIdx + 1),
                    icon: const Icon(Icons.arrow_forward, size: 18),
                    label: const Text('Suivant'),
                  )
                else
                  FilledButton.icon(
                    onPressed: _submitting ? null : _submitAttempt,
                    icon: _submitting
                        ? const SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.check, size: 18),
                    label: Text(_submitting ? 'Envoi...' : 'Soumettre'),
                    style: FilledButton.styleFrom(
                      backgroundColor: Colors.green,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuestionInput(Question question) {
    switch (question.questionType.toUpperCase()) {
      case 'MCQ':
        return _McqInput(
          question: question,
          answer: _answers[question.id] as String?,
          onChanged: (value) => _setAnswer(question.id, value),
        );
      case 'TRUE_FALSE':
        return _TrueFalseInput(
          answer: _answers[question.id] as bool?,
          onChanged: (value) => _setAnswer(question.id, value),
        );
      case 'FILL_IN':
        return _FillInInput(
          answer: _answers[question.id] as String? ?? '',
          onChanged: (value) => _setAnswer(question.id, value),
        );
      case 'DRAG_DROP':
        return _DragDropInput(
          question: question,
          answers: _answers[question.id] as Map<String, String>? ?? {},
          onChanged: (value) => _setAnswer(question.id, value),
        );
      case 'MATCHING':
        return _MatchingInput(
          question: question,
          answers: _answers[question.id] as Map<String, String>? ?? {},
          onChanged: (value) => _setAnswer(question.id, value),
        );
      default:
        return Text('Type de question non supporté: ${question.questionType}');
    }
  }

  Future<void> _showExitConfirm(BuildContext context) async {
    final exit = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Quitter le quiz ?'),
        content: const Text(
          'Vos réponses seront perdues si vous quittez maintenant.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Quitter'),
          ),
        ],
      ),
    );
    if (exit == true) _backToList();
  }
}

class _QuizTimerChip extends StatelessWidget {
  final int secondsLeft;

  const _QuizTimerChip({required this.secondsLeft});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isWarning = secondsLeft < 60;
    final color = isWarning ? Colors.red : theme.colorScheme.primary;

    return Semantics(
      label:
          'Time remaining ${secondsLeft ~/ 60} minutes ${secondsLeft % 60} seconds',
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isWarning
              ? Colors.red.withAlpha(25)
              : theme.colorScheme.primaryContainer,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.timer, size: 16, color: color),
            const SizedBox(width: 4),
            Text(
              '${(secondsLeft ~/ 60).toString().padLeft(2, '0')}:${(secondsLeft % 60).toString().padLeft(2, '0')}',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProgressDots extends StatelessWidget {
  final int total;
  final int current;
  final Map<String, dynamic> answered;
  final List<Question> questions;
  final ValueChanged<int> onTap;

  const _ProgressDots({
    required this.total,
    required this.current,
    required this.answered,
    required this.questions,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SizedBox(
      height: 56,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        itemCount: total,
        itemBuilder: (context, index) {
          final isAnswered = answered.containsKey(questions[index].id);
          final isCurrent = index == current;
          final stateLabel = isCurrent
              ? 'current'
              : isAnswered
                  ? 'answered'
                  : 'not answered';
          return Semantics(
            button: true,
            label: 'Question ${index + 1}',
            value: stateLabel,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2),
              child: SizedBox(
                width: 48,
                height: 48,
                child: InkWell(
                  onTap: () => onTap(index),
                  borderRadius: BorderRadius.circular(24),
                  child: Center(
                    child: Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isCurrent
                            ? theme.colorScheme.primary
                            : isAnswered
                                ? theme.colorScheme.primaryContainer
                                : theme.colorScheme.surfaceContainerHighest,
                        border: isCurrent
                            ? null
                            : Border.all(
                                color: isAnswered
                                    ? theme.colorScheme.primary
                                    : theme.colorScheme.outline.withAlpha(80),
                              ),
                      ),
                      child: Center(
                        child: Text(
                          '${index + 1}',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: isCurrent
                                ? Colors.white
                                : isAnswered
                                    ? theme.colorScheme.primary
                                    : theme.colorScheme.onSurface,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
