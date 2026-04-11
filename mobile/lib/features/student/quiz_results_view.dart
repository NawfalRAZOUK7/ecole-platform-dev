part of 'quiz_player_screen.dart';

extension _QuizResultsView on _QuizPlayerScreenState {
  Widget _buildResultsView(BuildContext context) {
    final theme = Theme.of(context);
    final result = _result!;
    final attempt = result.attempt;
    final score = attempt.score ?? 0;
    final maxScore = attempt.maxScore ?? 1;
    final percent = maxScore > 0 ? (score / maxScore * 100) : 0;
    final passed = percent >= 50;

    return Scaffold(
      appBar: AppBar(title: const Text('Résultats')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            color: passed
                ? theme.semanticPalette.successContainer
                : theme.colorScheme.errorContainer,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Icon(
                    passed ? Icons.emoji_events : Icons.sentiment_dissatisfied,
                    size: 56,
                    color: passed
                        ? theme.semanticPalette.success
                        : theme.colorScheme.error,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '${score.toStringAsFixed(0)}/${maxScore.toStringAsFixed(0)}',
                    style: theme.textTheme.headlineLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: passed
                          ? theme.semanticPalette.success
                          : theme.colorScheme.error,
                    ),
                  ),
                  Text(
                    '${percent.toStringAsFixed(0)}%',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: passed
                          ? theme.semanticPalette.success
                          : theme.colorScheme.error,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    passed ? 'Bravo !' : 'Continuez vos efforts !',
                    style: theme.textTheme.titleSmall,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Détails par question',
            style: theme.textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          ...result.responses.asMap().entries.map((entry) {
            final index = entry.key;
            final response = entry.value;
            final correct = response.isCorrect == true;

            return Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: correct
                                ? theme.semanticPalette.success.withAlpha(25)
                                : theme.colorScheme.error.withAlpha(25),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            correct ? Icons.check : Icons.close,
                            size: 18,
                            color: correct
                                ? theme.semanticPalette.success
                                : theme.colorScheme.error,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Q${index + 1}: ${response.questionText}',
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                        ),
                        Text(
                          '${(response.pointsEarned ?? 0).toStringAsFixed(0)}/${response.points}',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: correct
                                ? theme.semanticPalette.success
                                : theme.colorScheme.error,
                          ),
                        ),
                      ],
                    ),
                    if (response.studentAnswer != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Votre réponse: ${response.studentAnswer}',
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                    if (!correct && response.correctAnswer != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        'Réponse correcte: ${response.correctAnswer}',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.semanticPalette.success,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                    if (response.explanation != null) ...[
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(
                              Icons.lightbulb_outline,
                              size: 16,
                              color: theme.semanticPalette.warning,
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                response.explanation!,
                                style: theme.textTheme.bodySmall,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            );
          }),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _backToList,
            icon: const Icon(Icons.arrow_back),
            label: const Text('Retour aux quiz'),
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ],
      ),
    );
  }
}
