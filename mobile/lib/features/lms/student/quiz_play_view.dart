part of 'quiz_player_screen.dart';

extension _QuizPlayView on _QuizPlayerScreenState {
  Widget _buildPlayView(BuildContext context) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);
    final question = _questions[_currentIdx];
    final totalQuestions = _questions.length;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          tooltip: t.t('quiz.exit'),
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
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          question.questionText,
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w600),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.volume_up_outlined),
                        tooltip: t.t('quiz.listenQuestion'),
                        onPressed: () {
                          // Prefer the quiz's stored language; fall back to
                          // script detection (ar vs fr) for older quizzes.
                          final lang = _playingQuiz?.language ??
                              (RegExp(r'[؀-ۿ]').hasMatch(question.questionText)
                                  ? 'ar'
                                  : 'fr');
                          ref.read(ttsServiceProvider).speakWord(
                                question.questionText,
                                lang: lang,
                              );
                        },
                      ),
                    ],
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
                    label: Text(t.t('quiz.previous')),
                  )
                else
                  const SizedBox.shrink(),
                const Spacer(),
                if (_currentIdx < totalQuestions - 1)
                  FilledButton.icon(
                    onPressed: () => _goToQuestion(_currentIdx + 1),
                    icon: const Icon(Icons.arrow_forward, size: 18),
                    label: Text(t.t('quiz.next')),
                  )
                else
                  FilledButton.icon(
                    onPressed: _submitting ? null : _submitAttempt,
                    icon: _submitting
                        ? SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: theme.colorScheme.onPrimary,
                            ),
                          )
                        : const Icon(Icons.check, size: 18),
                    label: Text(
                      _submitting ? t.t('quiz.submitting') : t.t('quiz.submit'),
                    ),
                    style: FilledButton.styleFrom(
                      backgroundColor: theme.semanticPalette.success,
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
    final t = AppLocalizations.of(ref);
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
        return Text(
          t
              .t('quiz.unsupportedQuestionType')
              .replaceAll('{type}', question.questionType),
        );
    }
  }

  Future<void> _showExitConfirm(BuildContext context) async {
    final t = AppLocalizations.of(ref);
    final exit = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(t.t('quiz.exitTitle')),
        content: Text(t.t('quiz.exitMsg')),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(t.t('quiz.cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
            child: Text(t.t('quiz.exit')),
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
    final color =
        isWarning ? theme.colorScheme.error : theme.colorScheme.primary;

    return Semantics(
      label:
          'Time remaining ${secondsLeft ~/ 60} minutes ${secondsLeft % 60} seconds',
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isWarning
              ? theme.colorScheme.error.withAlpha(25)
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
                                ? theme.colorScheme.onPrimary
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
