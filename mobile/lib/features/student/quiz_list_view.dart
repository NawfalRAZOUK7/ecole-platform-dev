part of 'quiz_player_screen.dart';

extension _QuizListView on _QuizPlayerScreenState {
  Widget _buildListView(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Quiz')),
      body: _loadingList
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(_error!, textAlign: TextAlign.center),
                      const SizedBox(height: 16),
                      FilledButton.tonal(
                        onPressed: _fetchQuizzes,
                        child: const Text('Réessayer'),
                      ),
                    ],
                  ),
                )
              : _quizzes.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.quiz, size: 48, color: Colors.grey),
                          SizedBox(height: 16),
                          Text('Aucun quiz disponible'),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _fetchQuizzes,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _quizzes.length,
                        itemBuilder: (context, index) {
                          final quiz = _quizzes[index];
                          return _QuizCard(
                            quiz: quiz,
                            loading: _submitting,
                            onStart: () => _startQuiz(quiz),
                          );
                        },
                      ),
                    ),
    );
  }
}

class _QuizCard extends StatelessWidget {
  final Quiz quiz;
  final bool loading;
  final VoidCallback onStart;

  const _QuizCard({
    required this.quiz,
    required this.loading,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    quiz.title,
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ),
                _DifficultyBadge(difficulty: quiz.difficulty),
              ],
            ),
            if (quiz.description != null) ...[
              const SizedBox(height: 8),
              Text(quiz.description!, style: theme.textTheme.bodySmall),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                _InfoChip(
                  icon: Icons.help_outline,
                  label: '${quiz.questionCount} questions',
                ),
                _InfoChip(
                  icon: Icons.star_outline,
                  label: '${quiz.totalPoints} pts',
                ),
                if (quiz.timeLimitMinutes != null)
                  _InfoChip(
                    icon: Icons.timer,
                    label: '${quiz.timeLimitMinutes} min',
                  ),
                if (quiz.subject != null)
                  _InfoChip(icon: Icons.book, label: quiz.subject!),
              ],
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: loading ? null : onStart,
                icon: loading
                    ? const SizedBox(
                        height: 16,
                        width: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.play_arrow),
                label: const Text('Commencer'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DifficultyBadge extends StatelessWidget {
  final String difficulty;

  const _DifficultyBadge({required this.difficulty});

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (difficulty.toLowerCase()) {
      'easy' => (Colors.green, 'Facile'),
      'medium' => (Colors.orange, 'Moyen'),
      'hard' => (Colors.red, 'Difficile'),
      _ => (Colors.grey, difficulty),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _InfoChip({
    required this.icon,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: Colors.grey),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 12, color: Colors.grey),
        ),
      ],
    );
  }
}
