/// Riverpod state for the student academic-history feature (G49 Phase 3).
///
/// Three independent state notifiers — they fetch in parallel from the
/// same `programRepositoryProvider`. Each has a `refresh()` that
/// invalidates the corresponding cache prefix and reloads.
///
/// `studentId` is provided as the family parameter so the same screen
/// can be used by:
///   - STD viewing themselves (`studentId == auth.user.id`)
///   - PAR viewing a linked child
///   - ADM/DIR viewing any student in the school

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/academic/program.dart';

// ---------------------------------------------------------------------------
// Current program
// ---------------------------------------------------------------------------
class CurrentProgramState {
  final CurrentProgram? program;
  final bool isLoading;
  final String? error;

  const CurrentProgramState({
    this.program,
    this.isLoading = false,
    this.error,
  });

  CurrentProgramState copyWith({
    CurrentProgram? program,
    bool? isLoading,
    String? error,
    bool clearError = false,
  }) {
    return CurrentProgramState(
      program: program ?? this.program,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class CurrentProgramNotifier extends StateNotifier<CurrentProgramState> {
  final Ref _ref;
  final String _studentId;

  CurrentProgramNotifier(this._ref, this._studentId)
      : super(const CurrentProgramState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const CurrentProgramState(isLoading: true);
    try {
      final repo = _ref.read(programRepositoryProvider);
      final program = await repo.getCurrentProgram(_studentId);
      state = CurrentProgramState(program: program);
    } catch (e) {
      state = CurrentProgramState(error: e.toString());
    }
  }

  Future<void> refresh() async {
    await load();
  }
}

final currentProgramProvider = StateNotifierProvider.family<
    CurrentProgramNotifier, CurrentProgramState, String>(
  (ref, studentId) => CurrentProgramNotifier(ref, studentId),
);

// ---------------------------------------------------------------------------
// Academic timeline
// ---------------------------------------------------------------------------
class AcademicTimelineState {
  final List<AcademicTimelineEntry> items;
  final bool isLoading;
  final String? error;

  const AcademicTimelineState({
    this.items = const [],
    this.isLoading = false,
    this.error,
  });
}

class AcademicTimelineNotifier extends StateNotifier<AcademicTimelineState> {
  final Ref _ref;
  final String _studentId;

  AcademicTimelineNotifier(this._ref, this._studentId)
      : super(const AcademicTimelineState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const AcademicTimelineState(isLoading: true);
    try {
      final repo = _ref.read(programRepositoryProvider);
      final items = await repo.getAcademicTimeline(_studentId);
      state = AcademicTimelineState(items: items);
    } catch (e) {
      state = AcademicTimelineState(error: e.toString());
    }
  }

  Future<void> refresh() async {
    await _ref
        .read(cacheStoreProvider)
        .invalidatePrefix('program-timeline:$_studentId');
    await load();
  }
}

final academicTimelineProvider = StateNotifierProvider.family<
    AcademicTimelineNotifier, AcademicTimelineState, String>(
  (ref, studentId) => AcademicTimelineNotifier(ref, studentId),
);

// ---------------------------------------------------------------------------
// Program history (event log)
// ---------------------------------------------------------------------------
class ProgramHistoryState {
  final List<ProgramAssignmentEvent> events;
  final bool isLoading;
  final String? error;

  const ProgramHistoryState({
    this.events = const [],
    this.isLoading = false,
    this.error,
  });
}

class ProgramHistoryNotifier extends StateNotifier<ProgramHistoryState> {
  final Ref _ref;
  final String _studentId;

  ProgramHistoryNotifier(this._ref, this._studentId)
      : super(const ProgramHistoryState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const ProgramHistoryState(isLoading: true);
    try {
      final repo = _ref.read(programRepositoryProvider);
      final events = await repo.getProgramHistory(_studentId);
      state = ProgramHistoryState(events: events);
    } catch (e) {
      state = ProgramHistoryState(error: e.toString());
    }
  }

  Future<void> refresh() async {
    await _ref
        .read(cacheStoreProvider)
        .invalidatePrefix('program-history:$_studentId');
    await load();
  }
}

final programHistoryProvider = StateNotifierProvider.family<
    ProgramHistoryNotifier, ProgramHistoryState, String>(
  (ref, studentId) => ProgramHistoryNotifier(ref, studentId),
);

// ---------------------------------------------------------------------------
// Academic snapshots
// ---------------------------------------------------------------------------
class StudentSnapshotsState {
  final List<AcademicSnapshotSummary> snapshots;
  final bool isLoading;
  final String? error;

  const StudentSnapshotsState({
    this.snapshots = const [],
    this.isLoading = false,
    this.error,
  });
}

class StudentSnapshotsNotifier extends StateNotifier<StudentSnapshotsState> {
  final Ref _ref;
  final String _studentId;

  StudentSnapshotsNotifier(this._ref, this._studentId)
      : super(const StudentSnapshotsState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const StudentSnapshotsState(isLoading: true);
    try {
      final repo = _ref.read(programRepositoryProvider);
      final snapshots = await repo.getStudentSnapshots(_studentId);
      state = StudentSnapshotsState(snapshots: snapshots);
    } catch (e) {
      state = StudentSnapshotsState(error: e.toString());
    }
  }

  Future<void> refresh() async {
    await _ref
        .read(cacheStoreProvider)
        .invalidatePrefix('program-snapshots:$_studentId');
    await load();
  }
}

final studentSnapshotsProvider = StateNotifierProvider.family<
    StudentSnapshotsNotifier, StudentSnapshotsState, String>(
  (ref, studentId) => StudentSnapshotsNotifier(ref, studentId),
);
