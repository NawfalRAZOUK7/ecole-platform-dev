/// Timetable state management — Riverpod provider.
///
/// Reference: Phase 12B — Timetable screen state

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/academic/timetable.dart';

class TimetableState {
  final WeeklySchedule? schedule;
  final bool isLoading;
  final String? error;

  const TimetableState({this.schedule, this.isLoading = false, this.error});
}

class TimetableNotifier extends StateNotifier<TimetableState> {
  final Ref _ref;

  TimetableNotifier(this._ref) : super(const TimetableState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const TimetableState(isLoading: true);
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.get('/timetable/me/weekly');
      final data = resp.data;
      final schedule = WeeklySchedule.fromJson(data);
      state = TimetableState(schedule: schedule);
    } catch (e) {
      state = TimetableState(error: e.toString());
    }
  }

  Future<void> refresh() async {
    await _ref.read(cacheStoreProvider).invalidatePrefix('timetable:');
    await load();
  }
}

final timetableProvider =
    StateNotifierProvider<TimetableNotifier, TimetableState>((ref) {
  return TimetableNotifier(ref);
});
