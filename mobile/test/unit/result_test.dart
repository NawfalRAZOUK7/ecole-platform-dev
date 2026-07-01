/// Tests for lib/domain/entities/academic/result.dart
///
/// Covers:
///   - Required field construction
///   - All optional fields nullable
///   - Score and feedback presence/absence
///   - Status variations

import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/domain/entities/academic/result.dart';

void main() {
  group('Result', () {
    test('constructs with the minimum required fields', () {
      const result = Result(
        assignmentId: 'a-1',
        assignmentTitle: 'Devoir 1',
        courseTitle: 'Mathématiques',
        totalPoints: 20,
      );

      expect(result.assignmentId, 'a-1');
      expect(result.assignmentTitle, 'Devoir 1');
      expect(result.courseTitle, 'Mathématiques');
      expect(result.totalPoints, 20);
      // Optional fields default to null
      expect(result.submissionId, isNull);
      expect(result.status, isNull);
      expect(result.score, isNull);
      expect(result.feedbackText, isNull);
      expect(result.dueAt, isNull);
    });

    test('keeps a graded result with score and feedback', () {
      const result = Result(
        assignmentId: 'a-2',
        assignmentTitle: 'Devoir 2',
        courseTitle: 'Français',
        submissionId: 'sub-1',
        status: 'graded',
        score: 17.5,
        feedbackText: 'Bien joué !',
        totalPoints: 20,
        dueAt: '2026-05-30T23:59:00Z',
      );

      expect(result.submissionId, 'sub-1');
      expect(result.status, 'graded');
      expect(result.score, 17.5);
      expect(result.feedbackText, 'Bien joué !');
      expect(result.dueAt, '2026-05-30T23:59:00Z');
    });

    test('allows score of zero and full mark', () {
      const zero = Result(
        assignmentId: 'a-3',
        assignmentTitle: 'D',
        courseTitle: 'C',
        score: 0,
        totalPoints: 20,
      );
      const full = Result(
        assignmentId: 'a-3',
        assignmentTitle: 'D',
        courseTitle: 'C',
        score: 20,
        totalPoints: 20,
      );

      expect(zero.score, 0);
      expect(full.score, 20);
    });

    test('supports a pending status with no score', () {
      const result = Result(
        assignmentId: 'a-4',
        assignmentTitle: 'Devoir non rendu',
        courseTitle: 'Histoire',
        status: 'pending',
        totalPoints: 10,
      );

      expect(result.status, 'pending');
      expect(result.score, isNull);
    });
  });
}
