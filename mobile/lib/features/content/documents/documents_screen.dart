import 'dart:io';
import 'dart:ui' as ui;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/content/document_management.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/content/documents/document_preview_screen.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/widgets/signed_network_image.dart';

part 'documents_actions.dart';
part 'documents_tabs.dart';
part 'documents_widgets.dart';

const _resourceTypes = <String>[
  'lesson_plan',
  'worksheet',
  'presentation',
  'exam_template',
  'reference',
];

class DocumentsScreen extends ConsumerStatefulWidget {
  const DocumentsScreen({super.key});

  @override
  ConsumerState<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends ConsumerState<DocumentsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  final TextEditingController _resourceSearchController =
      TextEditingController();
  final TextEditingController _resourceSubjectController =
      TextEditingController();
  final TextEditingController _resourceLevelController =
      TextEditingController();

  bool _loading = true;
  bool _loadingMoreResources = false;
  bool _uploading = false;
  double _uploadProgress = 0;
  String _uploadLabel = '';
  String? _error;
  DocumentOptions _options = const DocumentOptions(
    categories: ['other'],
  );
  List<ManagedDocument> _myDocuments = [];
  List<ManagedDocument> _studentDocuments = [];
  List<StudentDocumentChecklistItem> _checklist = [];
  List<ResourceLibraryItem> _resources = [];
  String? _resourcesCursor;
  bool _resourcesHasMore = false;
  String _selectedStudentId = '';
  String _selectedCategory = '';
  String _selectedResourceType = '';
  double? _resourceMinRating;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _bootstrap();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _resourceSearchController.dispose();
    _resourceSubjectController.dispose();
    _resourceLevelController.dispose();
    super.dispose();
  }

  void _applyState(VoidCallback update) => setState(update);

  String get _role => ref.read(authProvider).user?.role ?? '';

  bool get _canUploadDocuments => {'PAR', 'ADM', 'DIR'}.contains(_role);

  bool get _canUploadResources => {'TCH', 'ADM', 'DIR'}.contains(_role);

  Future<void> _bootstrap() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = ref.read(documentRepositoryProvider);
      final options = await repo.getDocumentOptions();
      final selectedStudent = _selectedStudentId.isNotEmpty
          ? _selectedStudentId
          : (options.students.isNotEmpty ? options.students.first.id : '');

      final results = await Future.wait([
        repo.getMyDocuments(),
        repo.getResources(),
        if (selectedStudent.isNotEmpty)
          repo.getStudentDocuments(selectedStudent)
        else
          Future.value(<ManagedDocument>[]),
        if (selectedStudent.isNotEmpty)
          repo.getStudentChecklist(selectedStudent)
        else
          Future.value(<StudentDocumentChecklistItem>[]),
      ]);

      if (!mounted) return;
      final resourcePage = results[1]
          as dynamic; // Future.wait erases generic tuple types for PaginatedList
      setState(() {
        _options = options.categories.isEmpty
            ? const DocumentOptions(categories: ['other'])
            : options;
        _selectedStudentId = selectedStudent;
        _myDocuments = results[0] as List<ManagedDocument>;
        _resources = resourcePage.items as List<ResourceLibraryItem>;
        _resourcesCursor = resourcePage.nextCursor as String?;
        _resourcesHasMore = resourcePage.hasMore as bool;
        _studentDocuments = results[2] as List<ManagedDocument>;
        _checklist = results[3] as List<StudentDocumentChecklistItem>;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _reloadStudentData() async {
    if (_selectedStudentId.isEmpty) {
      setState(() {
        _studentDocuments = [];
        _checklist = [];
      });
      return;
    }
    try {
      final repo = ref.read(documentRepositoryProvider);
      final results = await Future.wait([
        repo.getStudentDocuments(_selectedStudentId),
        repo.getStudentChecklist(_selectedStudentId),
      ]);
      if (!mounted) return;
      setState(() {
        _studentDocuments = results[0] as List<ManagedDocument>;
        _checklist = results[1] as List<StudentDocumentChecklistItem>;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  Future<void> _reloadResources({bool reset = true}) async {
    if (reset) {
      setState(() {
        _loading = false;
        _loadingMoreResources = false;
      });
    }

    try {
      final response = await ref.read(documentRepositoryProvider).getResources(
            query: _resourceSearchController.text.trim().isEmpty
                ? null
                : _resourceSearchController.text.trim(),
            subject: _resourceSubjectController.text.trim().isEmpty
                ? null
                : _resourceSubjectController.text.trim(),
            level: _resourceLevelController.text.trim().isEmpty
                ? null
                : _resourceLevelController.text.trim(),
            type: _selectedResourceType.isEmpty ? null : _selectedResourceType,
            minRating: _resourceMinRating,
          );
      if (!mounted) return;
      setState(() {
        _resources = response.items;
        _resourcesCursor = response.nextCursor;
        _resourcesHasMore = response.hasMore;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  Future<void> _loadMoreResources() async {
    if (_loadingMoreResources ||
        !_resourcesHasMore ||
        _resourcesCursor == null ||
        _resourcesCursor!.isEmpty) {
      return;
    }
    setState(() => _loadingMoreResources = true);
    try {
      final response = await ref.read(documentRepositoryProvider).getResources(
            cursor: _resourcesCursor,
            query: _resourceSearchController.text.trim().isEmpty
                ? null
                : _resourceSearchController.text.trim(),
            subject: _resourceSubjectController.text.trim().isEmpty
                ? null
                : _resourceSubjectController.text.trim(),
            level: _resourceLevelController.text.trim().isEmpty
                ? null
                : _resourceLevelController.text.trim(),
            type: _selectedResourceType.isEmpty ? null : _selectedResourceType,
            minRating: _resourceMinRating,
          );
      if (!mounted) return;
      setState(() {
        _resources = [..._resources, ...response.items];
        _resourcesCursor = response.nextCursor;
        _resourcesHasMore = response.hasMore;
        _loadingMoreResources = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loadingMoreResources = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final textDirection =
        t.locale == 'ar' ? ui.TextDirection.rtl : ui.TextDirection.ltr;

    return Directionality(
      textDirection: textDirection,
      child: DefaultTabController(
        length: 3,
        child: Scaffold(
          appBar: AppBar(
            title: Text(t.t('documents.title')),
            bottom: TabBar(
              controller: _tabController,
              tabs: [
                Tab(text: t.t('documents.tabs.mine')),
                Tab(text: t.t('documents.tabs.student')),
                Tab(text: t.t('documents.tabs.resources')),
              ],
            ),
          ),
          body: _loading
              ? const Center(child: CircularProgressIndicator())
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildDocumentsTab(
                      title: t.t('documents.tabs.mine'),
                      items: _filteredDocuments(_myDocuments),
                      studentLinked: false,
                    ),
                    _buildStudentTab(),
                    _buildResourcesTab(),
                  ],
                ),
        ),
      ),
    );
  }
}
