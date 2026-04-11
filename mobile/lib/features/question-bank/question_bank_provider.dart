import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/question_bank.dart';

final questionBankSubjectFilterProvider = StateProvider<String?>((ref) => null);
final questionBankTypeFilterProvider = StateProvider<String?>((ref) => null);
final questionBankDifficultyFilterProvider =
    StateProvider<String?>((ref) => null);

final questionBankQuestionsProvider =
    FutureProvider<List<QuestionBankQuestion>>((ref) async {
  return ref.read(questionBankRepositoryProvider).listQuestions(
        subject: ref.watch(questionBankSubjectFilterProvider),
        type: ref.watch(questionBankTypeFilterProvider),
        difficulty: ref.watch(questionBankDifficultyFilterProvider),
      );
});

final questionBankStatsProvider =
    FutureProvider<QuestionBankStats>((ref) async {
  return ref.read(questionBankRepositoryProvider).getStats();
});
