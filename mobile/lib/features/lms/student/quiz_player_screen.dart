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
import 'package:ecole_platform/domain/entities/lms/quiz.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

part 'quiz_list_view.dart';
part 'quiz_play_view.dart';
part 'quiz_results_view.dart';
part 'quiz_inputs.dart';

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
}
