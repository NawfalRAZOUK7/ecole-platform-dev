class GradebookGrid {
  final String classId;
  final String className;
  final List<GradebookColumn> columns;
  final List<GradebookEntry> entries;

  const GradebookGrid({
    required this.classId,
    required this.className,
    this.columns = const [],
    this.entries = const [],
  });
}

class GradebookColumn {
  final String assessmentId;
  final String title;
  final double weight;
  final double maxScore;
  final String date;
  final String type;

  const GradebookColumn({
    required this.assessmentId,
    required this.title,
    required this.weight,
    this.maxScore = 20,
    required this.date,
    required this.type,
  });
}

class GradebookEntry {
  final String studentId;
  final String studentName;
  final Map<String, double?> grades;
  final double weightedAverage;

  const GradebookEntry({
    required this.studentId,
    required this.studentName,
    this.grades = const {},
    this.weightedAverage = 0,
  });
}

class GradeValueUpdate {
  final String studentId;
  final String assessmentId;
  final double value;

  const GradeValueUpdate({
    required this.studentId,
    required this.assessmentId,
    required this.value,
  });
}

class BulkGradeUpdate {
  final String classId;
  final List<GradeValueUpdate> grades;

  const BulkGradeUpdate({
    required this.classId,
    this.grades = const [],
  });
}

class WeightedAverageItem {
  final String studentId;
  final double avg;

  const WeightedAverageItem({
    required this.studentId,
    required this.avg,
  });
}

class WeightedSummary {
  final String classId;
  final String? periodId;
  final List<WeightedAverageItem> averages;

  const WeightedSummary({
    required this.classId,
    this.periodId,
    this.averages = const [],
  });
}

class StudentAssessmentGrade {
  final String assessmentId;
  final String title;
  final String type;
  final String date;
  final double maxScore;
  final double weight;
  final double? score;

  const StudentAssessmentGrade({
    required this.assessmentId,
    required this.title,
    required this.type,
    required this.date,
    this.maxScore = 20,
    required this.weight,
    this.score,
  });
}

class StudentGradeDetail {
  final String studentId;
  final String studentName;
  final String classId;
  final String className;
  final List<StudentAssessmentGrade> assessments;
  final double weightedAverage;

  const StudentGradeDetail({
    required this.studentId,
    required this.studentName,
    required this.classId,
    required this.className,
    this.assessments = const [],
    this.weightedAverage = 0,
  });
}

class GradeTranscript {
  final String studentId;
  final String studentName;
  final List<TranscriptPeriod> periods;

  const GradeTranscript({
    required this.studentId,
    required this.studentName,
    this.periods = const [],
  });
}

class TranscriptPeriod {
  final String periodId;
  final String label;
  final double weightedAverage;
  final List<TranscriptSubject> subjects;

  const TranscriptPeriod({
    required this.periodId,
    required this.label,
    required this.weightedAverage,
    this.subjects = const [],
  });
}

class TranscriptSubject {
  final String subjectId;
  final String subjectName;
  final double average;
  final List<StudentAssessmentGrade> grades;

  const TranscriptSubject({
    required this.subjectId,
    required this.subjectName,
    required this.average,
    this.grades = const [],
  });
}
