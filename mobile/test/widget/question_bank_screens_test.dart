import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/lms/question_bank.dart';
import 'package:ecole_platform/features/lms/question_bank/generate_quiz_screen.dart';
import 'package:ecole_platform/features/lms/question_bank/question_bank_import_screen.dart';
import 'package:ecole_platform/features/lms/question_bank/question_bank_screen.dart';

import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('QuestionBankScreen renders question list and stats',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final repository = MockQuestionBankRepository();
    when(
      () =>
          repository.listQuestions(subject: null, type: null, difficulty: null),
    ).thenAnswer((_) async => [_question]);
    when(() => repository.getStats()).thenAnswer(
      (_) async => const QuestionBankStats(
        total: 1,
        bySubject: {'Mathematics': 1},
        byType: {'mcq': 1},
        byDifficulty: {'medium': 1},
      ),
    );

    await pumpApp(
      tester,
      const QuestionBankScreen(),
      overrides: buildMockRepositoryOverrides(
        questionBankRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('What is 2 + 2?'), findsOneWidget);
    expect(find.text('Questions'), findsOneWidget);
  });

  testWidgets('GenerateQuizScreen renders generated quiz results',
      (tester) async {
    final repository = MockQuestionBankRepository();
    when(
      () => repository.generateQuiz(
        subject: 'Mathematics',
        difficulty: 'medium',
        count: 5,
        tags: const [],
      ),
    ).thenAnswer(
      (_) async => const GeneratedQuestionQuiz(
        total: 1,
        questions: [_question],
      ),
    );

    await pumpApp(
      tester,
      const GenerateQuizScreen(),
      overrides: buildMockRepositoryOverrides(
        questionBankRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).at(0), 'Mathematics');
    await tester.tap(find.byIcon(Icons.auto_awesome_outlined));
    await tester.pumpAndSettle();

    expect(find.text('Generated 1 question(s)'), findsOneWidget);
    expect(find.text('What is 2 + 2?'), findsOneWidget);
  });

  testWidgets('QuestionBankImportScreen renders import summary',
      (tester) async {
    final repository = MockQuestionBankRepository();
    when(() => repository.importFromQuiz('quiz-1')).thenAnswer(
      (_) async => const QuestionBankImportResult(
        imported: 3,
        skipped: 1,
        questions: [_question],
      ),
    );

    await pumpApp(
      tester,
      const QuestionBankImportScreen(),
      overrides: buildMockRepositoryOverrides(
        questionBankRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'quiz-1');
    await tester.tap(find.byIcon(Icons.upload_file_outlined));
    await tester.pumpAndSettle();

    expect(find.text('3'), findsOneWidget);
    expect(find.text('1'), findsOneWidget);
  });
}

const _question = QuestionBankQuestion(
  id: 'question-1',
  subject: 'Mathematics',
  type: 'mcq',
  difficulty: 'medium',
  text: 'What is 2 + 2?',
  choices: [
    QuestionBankChoice(id: 'choice-1', text: '4', isCorrect: true),
  ],
  correctAnswer: '4',
  tags: ['math'],
  createdBy: 'teacher-1',
  createdAt: '2026-04-12T08:00:00Z',
);
