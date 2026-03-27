/// Student quiz player — swipe-through questions, tap/drag answers,
/// all 5 question types, timer, progress dots, results with explanations.
///
/// Phase 10C: Mirrors web QuizPlayerPage.tsx (Phase 10B).
/// API: GET /quizzes, POST /quizzes/{id}/start, POST /attempts/{id}/respond,
///      POST /attempts/{id}/submit, GET /attempts/{id}/results
///
/// Question types: MCQ (radio), TRUE_FALSE (toggle), FILL_IN (text),
///   DRAG_DROP (drop zones), MATCHING (pair selection)

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/quiz.dart';

/// Views: list → playing → results
enum _View { list, playing, results }

class QuizPlayerScreen extends ConsumerStatefulWidget {
  const QuizPlayerScreen({super.key});

  @override
  ConsumerState<QuizPlayerScreen> createState() => _QuizPlayerScreenState();
}

class _QuizPlayerScreenState extends ConsumerState<QuizPlayerScreen> {
  _View _view = _View.list;
  String? _error;

  // Quiz list
  List<Quiz> _quizzes = [];
  bool _loadingList = true;

  // Playing state
  List<Question> _questions = [];
  QuizAttempt? _attempt;
  int _currentIdx = 0;
  final Map<String, dynamic> _answers = {};
  bool _submitting = false;

  // Results
  AttemptResult? _result;

  // Timer
  Timer? _timer;
  int _secondsLeft = 0;

  @override
  void initState() {
    super.initState();
    _fetchQuizzes();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // ── Quiz List ──

  Future<void> _fetchQuizzes() async {
    setState(() {
      _loadingList = true;
      _error = null;
    });
    try {
      final repo = ref.read(quizRepositoryProvider);
      _quizzes = await repo.getQuizzes();
      setState(() => _loadingList = false);
    } catch (e) {
      setState(() {
        _loadingList = false;
        _error = e.toString();
      });
    }
  }

  // ── Start Quiz ──

  Future<void> _startQuiz(Quiz quiz) async {
    setState(() {
      _error = null;
      _submitting = true;
    });
    try {
      final repo = ref.read(quizRepositoryProvider);

      // Try to get cached questions first, then fetch from API
      var questions = await repo.getCachedQuestions(quiz.id);
      questions ??= await repo.getQuizQuestions(quiz.id);

      // Cache for offline use
      await repo.cacheQuizForOffline(quiz.id, questions);

      final attempt = await repo.startAttempt(quiz.id);

      setState(() {
        _questions = questions!;
        _attempt = attempt;
        _currentIdx = 0;
        _answers.clear();
        _submitting = false;
        _view = _View.playing;
      });

      // Start timer if quiz has time limit
      if (quiz.timeLimitMinutes != null && attempt.startedAt != null) {
        final started = DateTime.parse(attempt.startedAt!);
        final endAt = started.add(Duration(minutes: quiz.timeLimitMinutes!));
        _startTimer(endAt);
      }
    } catch (e) {
      setState(() {
        _submitting = false;
        _error = e.toString();
      });
    }
  }

  void _startTimer(DateTime endAt) {
    _timer?.cancel();
    _updateTimerDisplay(endAt);
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      _updateTimerDisplay(endAt);
    });
  }

  void _updateTimerDisplay(DateTime endAt) {
    final now = DateTime.now();
    final diff = endAt.difference(now).inSeconds;
    if (diff <= 0) {
      _timer?.cancel();
      _submitAttempt(); // auto-submit
    } else {
      setState(() => _secondsLeft = diff);
    }
  }

  // ── Answer ──

  void _setAnswer(String questionId, dynamic answer) {
    setState(() => _answers[questionId] = answer);
  }

  // ── Navigate ──

  void _goToQuestion(int idx) {
    if (idx >= 0 && idx < _questions.length) {
      // Submit response for current question before navigating
      _submitCurrentResponse();
      setState(() => _currentIdx = idx);
    }
  }

  Future<void> _submitCurrentResponse() async {
    if (_attempt == null) return;
    final q = _questions[_currentIdx];
    final answer = _answers[q.id];
    if (answer == null) return;

    try {
      final repo = ref.read(quizRepositoryProvider);
      await repo.submitResponse(_attempt!.id, questionId: q.id, answer: answer);
    } catch (_) {
      // Queue for offline
      final queue = ref.read(offlineQueueProvider);
      await queue.enqueue(
        method: 'POST',
        path: '/attempts/${_attempt!.id}/respond',
        body: {'question_id': q.id, 'answer': answer},
      );
    }
  }

  // ── Submit ──

  Future<void> _submitAttempt() async {
    if (_attempt == null || _submitting) return;

    // Submit last response
    await _submitCurrentResponse();

    setState(() => _submitting = true);
    _timer?.cancel();

    try {
      final repo = ref.read(quizRepositoryProvider);
      await repo.submitAttempt(_attempt!.id);
      final result = await repo.getAttemptResults(_attempt!.id);
      setState(() {
        _result = result;
        _view = _View.results;
        _submitting = false;
      });
    } catch (e) {
      setState(() {
        _submitting = false;
        _error = 'Erreur de soumission: $e';
      });
    }
  }

  void _backToList() {
    _timer?.cancel();
    setState(() {
      _view = _View.list;
      _questions = [];
      _attempt = null;
      _result = null;
      _answers.clear();
      _secondsLeft = 0;
    });
    _fetchQuizzes();
  }

  @override
  Widget build(BuildContext context) {
    switch (_view) {
      case _View.list:
        return _buildListView(context);
      case _View.playing:
        return _buildPlayView(context);
      case _View.results:
        return _buildResultsView(context);
    }
  }

  // ══════════════════════════════════════════════════════════
  //  LIST VIEW
  // ══════════════════════════════════════════════════════════

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

  // ══════════════════════════════════════════════════════════
  //  PLAYING VIEW
  // ══════════════════════════════════════════════════════════

  Widget _buildPlayView(BuildContext context) {
    final theme = Theme.of(context);
    final q = _questions[_currentIdx];
    final totalQ = _questions.length;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => _showExitConfirm(context),
        ),
        title: Text('${_currentIdx + 1}/$totalQ'),
        actions: [
          // Timer
          if (_secondsLeft > 0)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 8),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _secondsLeft < 60
                    ? Colors.red.withAlpha(25)
                    : theme.colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.timer,
                      size: 16,
                      color: _secondsLeft < 60
                          ? Colors.red
                          : theme.colorScheme.primary),
                  const SizedBox(width: 4),
                  Text(
                    '${(_secondsLeft ~/ 60).toString().padLeft(2, '0')}:${(_secondsLeft % 60).toString().padLeft(2, '0')}',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _secondsLeft < 60
                          ? Colors.red
                          : theme.colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          // Progress dots
          _ProgressDots(
            total: totalQ,
            current: _currentIdx,
            answered: _answers,
            questions: _questions,
            onTap: _goToQuestion,
          ),

          // Question content
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Points badge
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${q.points} pt${q.points > 1 ? 's' : ''}',
                      style: TextStyle(
                        fontSize: 12,
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Question text
                  Text(
                    q.questionText,
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 24),

                  // Question input based on type
                  _buildQuestionInput(q),
                ],
              ),
            ),
          ),

          // Navigation bar
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
                // Previous
                if (_currentIdx > 0)
                  OutlinedButton.icon(
                    onPressed: () => _goToQuestion(_currentIdx - 1),
                    icon: const Icon(Icons.arrow_back, size: 18),
                    label: const Text('Précédent'),
                  )
                else
                  const SizedBox.shrink(),
                const Spacer(),
                // Next or Submit
                if (_currentIdx < totalQ - 1)
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
                                strokeWidth: 2, color: Colors.white),
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

  Widget _buildQuestionInput(Question q) {
    switch (q.questionType.toUpperCase()) {
      case 'MCQ':
        return _McqInput(
          question: q,
          answer: _answers[q.id] as String?,
          onChanged: (v) => _setAnswer(q.id, v),
        );
      case 'TRUE_FALSE':
        return _TrueFalseInput(
          answer: _answers[q.id] as bool?,
          onChanged: (v) => _setAnswer(q.id, v),
        );
      case 'FILL_IN':
        return _FillInInput(
          answer: _answers[q.id] as String? ?? '',
          onChanged: (v) => _setAnswer(q.id, v),
        );
      case 'DRAG_DROP':
        return _DragDropInput(
          question: q,
          answers: _answers[q.id] as Map<String, String>? ?? {},
          onChanged: (v) => _setAnswer(q.id, v),
        );
      case 'MATCHING':
        return _MatchingInput(
          question: q,
          answers: _answers[q.id] as Map<String, String>? ?? {},
          onChanged: (v) => _setAnswer(q.id, v),
        );
      default:
        return Text('Type de question non supporté: ${q.questionType}');
    }
  }

  Future<void> _showExitConfirm(BuildContext context) async {
    final exit = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Quitter le quiz ?'),
        content: const Text(
            'Vos réponses seront perdues si vous quittez maintenant.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Quitter'),
          ),
        ],
      ),
    );
    if (exit == true) _backToList();
  }

  // ══════════════════════════════════════════════════════════
  //  RESULTS VIEW
  // ══════════════════════════════════════════════════════════

  Widget _buildResultsView(BuildContext context) {
    final theme = Theme.of(context);
    final res = _result!;
    final attempt = res.attempt;
    final score = attempt.score ?? 0;
    final maxScore = attempt.maxScore ?? 1;
    final pct = maxScore > 0 ? (score / maxScore * 100) : 0;
    final passed = pct >= 50;

    return Scaffold(
      appBar: AppBar(title: const Text('Résultats')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Score summary
          Card(
            color: passed ? Colors.green.shade50 : Colors.red.shade50,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Icon(
                    passed ? Icons.emoji_events : Icons.sentiment_dissatisfied,
                    size: 56,
                    color: passed ? Colors.green : Colors.red,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '${score.toStringAsFixed(0)}/${maxScore.toStringAsFixed(0)}',
                    style: theme.textTheme.headlineLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: passed ? Colors.green : Colors.red,
                    ),
                  ),
                  Text(
                    '${pct.toStringAsFixed(0)}%',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: passed ? Colors.green : Colors.red,
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

          // Per-question breakdown
          Text(
            'Détails par question',
            style: theme.textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          ...res.responses.asMap().entries.map((entry) {
            final idx = entry.key;
            final r = entry.value;
            final correct = r.isCorrect == true;

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
                                ? Colors.green.withAlpha(25)
                                : Colors.red.withAlpha(25),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            correct ? Icons.check : Icons.close,
                            size: 18,
                            color: correct ? Colors.green : Colors.red,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Q${idx + 1}: ${r.questionText}',
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                        ),
                        Text(
                          '${(r.pointsEarned ?? 0).toStringAsFixed(0)}/${r.points}',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: correct ? Colors.green : Colors.red,
                          ),
                        ),
                      ],
                    ),
                    if (r.studentAnswer != null) ...[
                      const SizedBox(height: 8),
                      Text('Votre réponse: ${r.studentAnswer}',
                          style: theme.textTheme.bodySmall),
                    ],
                    if (!correct && r.correctAnswer != null) ...[
                      const SizedBox(height: 4),
                      Text('Réponse correcte: ${r.correctAnswer}',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: Colors.green,
                            fontWeight: FontWeight.w600,
                          )),
                    ],
                    if (r.explanation != null) ...[
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
                            const Icon(Icons.lightbulb_outline,
                                size: 16, color: Colors.orange),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(r.explanation!,
                                  style: theme.textTheme.bodySmall),
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

// ══════════════════════════════════════════════════════════
//  SUB-WIDGETS
// ══════════════════════════════════════════════════════════

// ── Quiz Card ──

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
                  child: Text(quiz.title,
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.bold)),
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
                    label: '${quiz.questionCount} questions'),
                _InfoChip(
                    icon: Icons.star_outline, label: '${quiz.totalPoints} pts'),
                if (quiz.timeLimitMinutes != null)
                  _InfoChip(
                      icon: Icons.timer, label: '${quiz.timeLimitMinutes} min'),
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
                            strokeWidth: 2, color: Colors.white),
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
      child: Text(label,
          style: TextStyle(
              fontSize: 11, color: color, fontWeight: FontWeight.w600)),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _InfoChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: Colors.grey),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }
}

// ── Progress Dots ──

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
    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: total,
        itemBuilder: (context, index) {
          final isAnswered = answered.containsKey(questions[index].id);
          final isCurrent = index == current;
          return GestureDetector(
            onTap: () => onTap(index),
            child: Container(
              width: 28,
              height: 28,
              margin: const EdgeInsets.symmetric(horizontal: 2),
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
          );
        },
      ),
    );
  }
}

// ── MCQ Input (tap option cards) ──

class _McqInput extends StatelessWidget {
  final Question question;
  final String? answer;
  final ValueChanged<String> onChanged;

  const _McqInput({
    required this.question,
    this.answer,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final choices = question.options?['choices'] as List<dynamic>? ?? [];

    return Column(
      children: choices.map((choice) {
        final label = choice is Map
            ? (choice['label'] ?? choice['text'] ?? '') as String
            : choice.toString();
        final value = choice is Map
            ? (choice['value'] ?? choice['key'] ?? label) as String
            : choice.toString();
        final selected = answer == value;

        return GestureDetector(
          onTap: () => onChanged(value),
          child: Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: selected
                  ? theme.colorScheme.primaryContainer
                  : theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: selected
                    ? theme.colorScheme.primary
                    : theme.colorScheme.outline,
                width: selected ? 2 : 1,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  selected
                      ? Icons.radio_button_checked
                      : Icons.radio_button_off,
                  color: selected ? theme.colorScheme.primary : Colors.grey,
                  size: 22,
                ),
                const SizedBox(width: 12),
                Expanded(
                    child: Text(label, style: const TextStyle(fontSize: 15))),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ── True/False Toggle ──

class _TrueFalseInput extends StatelessWidget {
  final bool? answer;
  final ValueChanged<bool> onChanged;

  const _TrueFalseInput({
    this.answer,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
            child:
                _toggleCard(context, true, 'Vrai', Icons.check_circle_outline)),
        const SizedBox(width: 16),
        Expanded(
            child: _toggleCard(context, false, 'Faux', Icons.cancel_outlined)),
      ],
    );
  }

  Widget _toggleCard(
      BuildContext context, bool value, String label, IconData icon) {
    final theme = Theme.of(context);
    final selected = answer == value;

    return GestureDetector(
      onTap: () => onChanged(value),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 32),
        decoration: BoxDecoration(
          color: selected
              ? (value ? Colors.green.withAlpha(25) : Colors.red.withAlpha(25))
              : theme.colorScheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: selected
                ? (value ? Colors.green : Colors.red)
                : theme.colorScheme.outline,
            width: selected ? 2 : 1,
          ),
        ),
        child: Column(
          children: [
            Icon(icon,
                size: 40,
                color: selected
                    ? (value ? Colors.green : Colors.red)
                    : Colors.grey),
            const SizedBox(height: 8),
            Text(label,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: selected
                      ? (value ? Colors.green : Colors.red)
                      : Colors.grey,
                )),
          ],
        ),
      ),
    );
  }
}

// ── Fill-in Text Input ──

class _FillInInput extends StatelessWidget {
  final String answer;
  final ValueChanged<String> onChanged;

  const _FillInInput({
    required this.answer,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      initialValue: answer,
      onChanged: onChanged,
      decoration: const InputDecoration(
        labelText: 'Votre réponse',
        hintText: 'Tapez votre réponse ici...',
        border: OutlineInputBorder(),
      ),
      maxLines: 3,
    );
  }
}

// ── Drag & Drop (simplified: dropdown for each zone) ──

class _DragDropInput extends StatelessWidget {
  final Question question;
  final Map<String, String> answers;
  final ValueChanged<Map<String, String>> onChanged;

  const _DragDropInput({
    required this.question,
    required this.answers,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final zones = question.options?['zones'] as List<dynamic>? ?? [];
    final items = question.options?['items'] as List<dynamic>? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Faites glisser les éléments vers les zones :',
            style: theme.textTheme.bodySmall),
        const SizedBox(height: 12),
        ...zones.map((zone) {
          final zoneName = zone is Map
              ? (zone['label'] ?? zone['id'] ?? '') as String
              : zone.toString();
          final zoneId = zone is Map
              ? (zone['id'] ?? zone['label'] ?? '') as String
              : zone.toString();

          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: Text(zoneName,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 3,
                  child: DropdownButtonFormField<String>(
                    initialValue: answers[zoneId],
                    decoration: InputDecoration(
                      border: const OutlineInputBorder(),
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 8),
                      hintText: 'Sélectionner...',
                      fillColor: theme.colorScheme.surface,
                    ),
                    items: items.map((item) {
                      final label = item is Map
                          ? (item['label'] ?? item['text'] ?? '') as String
                          : item.toString();
                      return DropdownMenuItem(
                          value: label,
                          child: Text(label,
                              style: const TextStyle(fontSize: 13)));
                    }).toList(),
                    onChanged: (v) {
                      if (v != null) {
                        final updated = Map<String, String>.from(answers);
                        updated[zoneId] = v;
                        onChanged(updated);
                      }
                    },
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }
}

// ── Matching (tap pairs) ──

class _MatchingInput extends StatelessWidget {
  final Question question;
  final Map<String, String> answers;
  final ValueChanged<Map<String, String>> onChanged;

  const _MatchingInput({
    required this.question,
    required this.answers,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final leftItems = question.options?['left'] as List<dynamic>? ?? [];
    final rightItems = question.options?['right'] as List<dynamic>? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Associez chaque élément de gauche avec celui de droite :',
            style: theme.textTheme.bodySmall),
        const SizedBox(height: 12),
        ...leftItems.map((left) {
          final leftLabel = left is Map
              ? (left['label'] ?? left['text'] ?? '') as String
              : left.toString();
          final leftId = left is Map
              ? (left['id'] ?? left['label'] ?? '') as String
              : left.toString();

          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(leftLabel,
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 8),
                  child:
                      Icon(Icons.arrow_forward, size: 18, color: Colors.grey),
                ),
                Expanded(
                  flex: 3,
                  child: DropdownButtonFormField<String>(
                    initialValue: answers[leftId],
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      hintText: 'Sélectionner...',
                    ),
                    items: rightItems.map((right) {
                      final label = right is Map
                          ? (right['label'] ?? right['text'] ?? '') as String
                          : right.toString();
                      return DropdownMenuItem(
                          value: label,
                          child: Text(label,
                              style: const TextStyle(fontSize: 13)));
                    }).toList(),
                    onChanged: (v) {
                      if (v != null) {
                        final updated = Map<String, String>.from(answers);
                        updated[leftId] = v;
                        onChanged(updated);
                      }
                    },
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }
}
