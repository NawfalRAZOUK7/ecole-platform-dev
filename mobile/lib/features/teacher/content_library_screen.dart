/// Teacher content library — browse + assign content to class, upload from phone,
/// submit for platform review, view my submissions.
///
/// Phase 10C: Mirrors web ContentLibraryPage.tsx (Phase 10B).
/// API: GET /content/library, POST /content/assign, POST /content/submit-for-review,
///      GET /content/my-submissions, POST /content-items/upload

import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/quiz.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/shared/widgets/search_filter_bar.dart';

part 'content_filters.dart';
part 'content_card.dart';
part 'upload_form.dart';
part 'submissions_tab.dart';

// ── Provider ──

class _LibraryState {
  final List<LibraryItem> items;
  final bool isLoading;
  final String? error;
  final String? typeFilter;
  final String? levelFilter;
  final String? originFilter;

  const _LibraryState({
    this.items = const [],
    this.isLoading = false,
    this.error,
    this.typeFilter,
    this.levelFilter,
    this.originFilter,
  });
}

class _LibraryNotifier extends StateNotifier<_LibraryState> {
  final Ref _ref;

  _LibraryNotifier(this._ref) : super(const _LibraryState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = _LibraryState(
      isLoading: true,
      typeFilter: state.typeFilter,
      levelFilter: state.levelFilter,
      originFilter: state.originFilter,
    );
    try {
      final repo = _ref.read(contentLibraryRepositoryProvider);
      final result = await repo.browseLibrary(
        contentType: state.typeFilter,
        level: state.levelFilter,
        origin: state.originFilter,
      );
      state = _LibraryState(
        items: result.items,
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
        originFilter: state.originFilter,
      );
    } catch (e) {
      state = _LibraryState(
        error: e.toString(),
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
        originFilter: state.originFilter,
      );
    }
  }

  void setTypeFilter(String? v) {
    state = _LibraryState(
        typeFilter: v,
        levelFilter: state.levelFilter,
        originFilter: state.originFilter);
    load();
  }

  void setLevelFilter(String? v) {
    state = _LibraryState(
        typeFilter: state.typeFilter,
        levelFilter: v,
        originFilter: state.originFilter);
    load();
  }

  void setOriginFilter(String? v) {
    state = _LibraryState(
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
        originFilter: v);
    load();
  }
}

final _libraryProvider =
    StateNotifierProvider<_LibraryNotifier, _LibraryState>((ref) {
  return _LibraryNotifier(ref);
});

// ── Screen ──

class ContentLibraryScreen extends ConsumerStatefulWidget {
  const ContentLibraryScreen({super.key});

  @override
  ConsumerState<ContentLibraryScreen> createState() =>
      _ContentLibraryScreenState();
}

class _ContentLibraryScreenState extends ConsumerState<ContentLibraryScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bibliothèque de contenu'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Parcourir'),
            Tab(text: 'Téléverser'),
            Tab(text: 'Soumissions'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _BrowseTab(),
          _UploadTab(),
          _SubmissionsTab(),
        ],
      ),
    );
  }
}
