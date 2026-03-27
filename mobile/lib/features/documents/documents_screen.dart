import 'dart:io';
import 'dart:ui' as ui;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/document_management.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/documents/document_preview_screen.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

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

  Future<void> _pickAndUploadDocument({
    required bool fromCamera,
    required bool studentLinked,
  }) async {
    final file = fromCamera ? await _pickImageFromCamera() : await _pickFile();
    if (file == null) return;

    final selection = await _showDocumentUploadSheet(
      initialCategory: _selectedCategory.isEmpty ? 'other' : _selectedCategory,
    );
    if (selection == null) return;

    setState(() {
      _uploading = true;
      _uploadProgress = 0;
      _uploadLabel = selection.$1;
      _error = null;
    });

    try {
      await ref.read(documentRepositoryProvider).uploadDocument(
            file: file,
            category: selection.$1,
            linkedStudentId: studentLinked && _selectedStudentId.isNotEmpty
                ? _selectedStudentId
                : null,
            expiresAt: selection.$2,
            onProgress: (sent, total) {
              if (!mounted || total <= 0) return;
              setState(() {
                _uploadProgress = sent / total;
              });
            },
          );

      if (!mounted) return;
      await Future.wait([
        _bootstrap(),
        if (studentLinked) _reloadStudentData(),
      ]);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content:
                Text(AppLocalizations.of(ref).t('documents.uploadSuccess'))),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (!mounted) return;
      setState(() {
        _uploading = false;
        _uploadProgress = 0;
        _uploadLabel = '';
      });
    }
  }

  Future<void> _pickAndUploadResource() async {
    final file = await _pickFile();
    if (file == null) return;

    final payload = await _showResourceUploadSheet(file.path.split('/').last);
    if (payload == null) return;

    setState(() {
      _uploading = true;
      _uploadProgress = 0;
      _uploadLabel = payload.title;
      _error = null;
    });

    try {
      await ref.read(documentRepositoryProvider).uploadResource(
            file: file,
            title: payload.title,
            description: payload.description,
            subject: payload.subject,
            level: payload.level,
            type: payload.type,
            tags: payload.tags,
            visibility: 'school',
            onProgress: (sent, total) {
              if (!mounted || total <= 0) return;
              setState(() => _uploadProgress = sent / total);
            },
          );
      if (!mounted) return;
      await _reloadResources();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content:
                Text(AppLocalizations.of(ref).t('documents.resourceUploaded'))),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (!mounted) return;
      setState(() {
        _uploading = false;
        _uploadProgress = 0;
        _uploadLabel = '';
      });
    }
  }

  Future<void> _openDocumentPreview(ManagedDocument document) async {
    if (!document.isImage && !document.isPdf) {
      await _shareDocument(document);
      return;
    }
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => DocumentPreviewScreen(document: document),
      ),
    );
    await _bootstrap();
  }

  Future<void> _openResource(ResourceLibraryItem resource) async {
    final document = resource.document;
    if (document == null || (!document.isImage && !document.isPdf)) {
      await _shareResource(resource);
      return;
    }
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => DocumentPreviewScreen(resource: resource),
      ),
    );
    await _reloadResources();
  }

  Future<void> _shareDocument(ManagedDocument document) async {
    try {
      final file = await ref
          .read(documentRepositoryProvider)
          .downloadDocumentFile(document);
      await Share.shareXFiles(
        [XFile(file.path)],
        text: document.originalFilename,
      );
      await _bootstrap();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _shareResource(ResourceLibraryItem resource) async {
    try {
      final file = await ref
          .read(documentRepositoryProvider)
          .downloadResourceFile(resource);
      await Share.shareXFiles(
        [XFile(file.path)],
        text: resource.title,
      );
      await _reloadResources();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _deleteDocument(ManagedDocument document,
      {bool hardDelete = false}) async {
    final confirmed = await _confirmDelete();
    if (!confirmed) return;
    try {
      await ref.read(documentRepositoryProvider).deleteDocument(
            document.id,
            hardDelete: hardDelete,
          );
      await _bootstrap();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _deleteResource(ResourceLibraryItem resource) async {
    final confirmed = await _confirmDelete();
    if (!confirmed) return;
    try {
      await ref.read(documentRepositoryProvider).deleteResource(resource.id);
      await _reloadResources();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _rateResource(ResourceLibraryItem resource) async {
    final rating = await _showRatingDialog(resource.myRating);
    if (rating == null) return;
    try {
      final summary = await ref
          .read(documentRepositoryProvider)
          .rateResource(resource.id, rating);
      if (!mounted) return;
      setState(() {
        _resources = _resources
            .map((item) => item.id == resource.id
                ? item.copyWith(
                    myRating: summary.myRating ?? rating,
                    avgRating: summary.avgRating,
                    ratingCount: summary.ratingCount,
                  )
                : item)
            .toList();
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<bool> _confirmDelete() async {
    final t = AppLocalizations.of(ref);
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(t.t('documents.delete')),
            content: Text(t.t('documents.confirmDelete')),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: Text(t.t('common.cancel')),
              ),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: Text(t.t('documents.delete')),
              ),
            ],
          ),
        ) ??
        false;
  }

  Future<File?> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const [
        'pdf',
        'docx',
        'xlsx',
        'pptx',
        'png',
        'jpg',
        'jpeg',
        'webp',
        'zip',
      ],
    );
    final path = result?.files.single.path;
    if (path == null || path.isEmpty) return null;
    return File(path);
  }

  Future<File?> _pickImageFromCamera() async {
    final image = await ImagePicker().pickImage(
      source: ImageSource.camera,
      imageQuality: 92,
    );
    if (image == null) return null;
    return File(image.path);
  }

  Future<(String, String?)?> _showDocumentUploadSheet({
    required String initialCategory,
  }) async {
    final t = AppLocalizations.of(ref);
    final categories =
        _options.categories.isEmpty ? const ['other'] : _options.categories;

    String selectedCategory = categories.contains(initialCategory)
        ? initialCategory
        : categories.first;
    DateTime? expiryDate;

    return showModalBottomSheet<(String, String?)>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    t.t('documents.uploadMetadata'),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: selectedCategory,
                    decoration: InputDecoration(
                      labelText: t.t('documents.category'),
                    ),
                    items: categories
                        .map(
                          (item) => DropdownMenuItem(
                            value: item,
                            child: Text(t.t('documents.categories.$item')),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      if (value == null) return;
                      setModalState(() => selectedCategory = value);
                    },
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: () async {
                      final selected = await showDatePicker(
                        context: context,
                        initialDate: expiryDate ?? DateTime.now(),
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2100),
                        locale: Locale(ref.read(localeProvider)),
                      );
                      if (selected == null) return;
                      setModalState(() => expiryDate = selected);
                    },
                    icon: const Icon(Icons.event_outlined),
                    label: Text(
                      expiryDate == null
                          ? t.t('documents.addExpiry')
                          : DateFormat.yMMMd(ref.read(localeProvider))
                              .format(expiryDate!),
                    ),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: () {
                        Navigator.of(context).pop(
                          (
                            selectedCategory,
                            expiryDate?.toIso8601String(),
                          ),
                        );
                      },
                      child: Text(t.t('documents.upload')),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Future<_ResourceUploadPayload?> _showResourceUploadSheet(
    String initialTitle,
  ) async {
    final t = AppLocalizations.of(ref);
    final titleController = TextEditingController(text: initialTitle);
    final descriptionController = TextEditingController();
    final subjectController = TextEditingController(
      text: _resourceSubjectController.text,
    );
    final levelController = TextEditingController(
      text: _resourceLevelController.text,
    );
    final tagsController = TextEditingController();
    String selectedType = _selectedResourceType.isNotEmpty
        ? _selectedResourceType
        : _resourceTypes.first;

    final result = await showModalBottomSheet<_ResourceUploadPayload>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              ),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      t.t('documents.resourceUpload'),
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: titleController,
                      decoration: InputDecoration(
                        labelText: t.t('documents.resourceTitle'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: descriptionController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        labelText: t.t('documents.description'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: subjectController,
                      decoration: InputDecoration(
                        labelText: t.t('documents.subject'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: levelController,
                      decoration: InputDecoration(
                        labelText: t.t('documents.level'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: selectedType,
                      decoration: InputDecoration(
                        labelText: t.t('documents.type'),
                      ),
                      items: _resourceTypes
                          .map(
                            (item) => DropdownMenuItem(
                              value: item,
                              child: Text(t.t('documents.resourceTypes.$item')),
                            ),
                          )
                          .toList(),
                      onChanged: (value) {
                        if (value == null) return;
                        setModalState(() => selectedType = value);
                      },
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: tagsController,
                      decoration: InputDecoration(
                        labelText: t.t('documents.tags'),
                        hintText: t.t('documents.tagsHint'),
                      ),
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: () {
                          Navigator.of(context).pop(
                            _ResourceUploadPayload(
                              title: titleController.text.trim().isEmpty
                                  ? initialTitle
                                  : titleController.text.trim(),
                              description: descriptionController.text.trim(),
                              subject: subjectController.text.trim(),
                              level: levelController.text.trim(),
                              type: selectedType,
                              tags: tagsController.text
                                  .split(',')
                                  .map((item) => item.trim())
                                  .where((item) => item.isNotEmpty)
                                  .toList(),
                            ),
                          );
                        },
                        child: Text(t.t('documents.upload')),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );

    titleController.dispose();
    descriptionController.dispose();
    subjectController.dispose();
    levelController.dispose();
    tagsController.dispose();
    return result;
  }

  Future<int?> _showRatingDialog(int? currentRating) async {
    final t = AppLocalizations.of(ref);
    int selectedRating = currentRating ?? 5;
    return showDialog<int>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(t.t('documents.rate')),
          content: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              5,
              (index) => IconButton(
                onPressed: () =>
                    setDialogState(() => selectedRating = index + 1),
                icon: Icon(
                  index < selectedRating ? Icons.star : Icons.star_border,
                  color: Colors.amber,
                ),
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(t.t('common.cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(selectedRating),
              child: Text(t.t('documents.save')),
            ),
          ],
        ),
      ),
    );
  }

  List<ManagedDocument> _filteredDocuments(List<ManagedDocument> items) {
    if (_selectedCategory.isEmpty) return items;
    return items.where((item) => item.category == _selectedCategory).toList();
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

  Widget _buildDocumentsTab({
    required String title,
    required List<ManagedDocument> items,
    required bool studentLinked,
  }) {
    final t = AppLocalizations.of(ref);

    return RefreshIndicator(
      onRefresh: _bootstrap,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            _ErrorCard(message: _error!),
            const SizedBox(height: 12),
          ],
          if (_uploading) ...[
            _UploadProgressCard(
              title: _uploadLabel.isEmpty
                  ? t.t('documents.uploading')
                  : _uploadLabel,
              progress: _uploadProgress,
            ),
            const SizedBox(height: 12),
          ],
          _CategoryChipBar(
            categories: _options.categories,
            selected: _selectedCategory,
            onChanged: (value) {
              setState(() => _selectedCategory = value);
            },
          ),
          if (_canUploadDocuments) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: () => _pickAndUploadDocument(
                    fromCamera: false,
                    studentLinked: studentLinked,
                  ),
                  icon: const Icon(Icons.attach_file_outlined),
                  label: Text(t.t('documents.pickFile')),
                ),
                OutlinedButton.icon(
                  onPressed: () => _pickAndUploadDocument(
                    fromCamera: true,
                    studentLinked: studentLinked,
                  ),
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: Text(t.t('documents.scan')),
                ),
              ],
            ),
          ],
          const SizedBox(height: 16),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          if (items.isEmpty)
            Center(child: Text(t.t('documents.empty')))
          else
            ...items.map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _DocumentCard(
                  item: item,
                  locale: ref.read(localeProvider),
                  onTap: () => _openDocumentPreview(item),
                  onShare: () => _shareDocument(item),
                  onDelete: item.canDelete
                      ? () => _deleteDocument(
                            item,
                            hardDelete: item.canHardDelete,
                          )
                      : null,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildStudentTab() {
    final t = AppLocalizations.of(ref);
    return RefreshIndicator(
      onRefresh: () async {
        await _bootstrap();
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            _ErrorCard(message: _error!),
            const SizedBox(height: 12),
          ],
          if (_options.students.isEmpty)
            Center(child: Text(t.t('documents.noStudents')))
          else ...[
            DropdownButtonFormField<String>(
              key: ValueKey(_selectedStudentId),
              initialValue: _selectedStudentId.isEmpty
                  ? _options.students.first.id
                  : _selectedStudentId,
              decoration: InputDecoration(
                labelText: t.t('documents.studentSelector'),
              ),
              items: _options.students
                  .map(
                    (item) => DropdownMenuItem<String>(
                      value: item.id,
                      child: Text(item.fullName),
                    ),
                  )
                  .toList(),
              onChanged: (value) {
                if (value == null || value == _selectedStudentId) return;
                setState(() => _selectedStudentId = value);
                _reloadStudentData();
              },
            ),
            const SizedBox(height: 12),
            _CategoryChipBar(
              categories: _options.categories,
              selected: _selectedCategory,
              onChanged: (value) {
                setState(() => _selectedCategory = value);
              },
            ),
            if (_canUploadDocuments) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: _selectedStudentId.isEmpty
                        ? null
                        : () => _pickAndUploadDocument(
                              fromCamera: false,
                              studentLinked: true,
                            ),
                    icon: const Icon(Icons.attach_file_outlined),
                    label: Text(t.t('documents.pickFile')),
                  ),
                  OutlinedButton.icon(
                    onPressed: _selectedStudentId.isEmpty
                        ? null
                        : () => _pickAndUploadDocument(
                              fromCamera: true,
                              studentLinked: true,
                            ),
                    icon: const Icon(Icons.camera_alt_outlined),
                    label: Text(t.t('documents.scan')),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 16),
            Text(
              t.t('documents.checklist'),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            if (_checklist.isEmpty)
              Center(child: Text(t.t('documents.empty')))
            else
              ..._checklist.map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _ChecklistCard(
                    item: item,
                    locale: ref.read(localeProvider),
                  ),
                ),
              ),
            const SizedBox(height: 16),
            Text(
              t.t('documents.studentDocuments'),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            if (_studentDocuments.isEmpty)
              Center(child: Text(t.t('documents.empty')))
            else
              ..._filteredDocuments(_studentDocuments).map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _DocumentCard(
                    item: item,
                    locale: ref.read(localeProvider),
                    onTap: () => _openDocumentPreview(item),
                    onShare: () => _shareDocument(item),
                    onDelete: item.canDelete
                        ? () => _deleteDocument(
                              item,
                              hardDelete: item.canHardDelete,
                            )
                        : null,
                  ),
                ),
              ),
          ],
        ],
      ),
    );
  }

  Widget _buildResourcesTab() {
    final t = AppLocalizations.of(ref);

    return RefreshIndicator(
      onRefresh: () async {
        await _reloadResources();
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            _ErrorCard(message: _error!),
            const SizedBox(height: 12),
          ],
          if (_uploading) ...[
            _UploadProgressCard(
              title: _uploadLabel.isEmpty
                  ? t.t('documents.uploading')
                  : _uploadLabel,
              progress: _uploadProgress,
            ),
            const SizedBox(height: 12),
          ],
          TextField(
            controller: _resourceSearchController,
            decoration: InputDecoration(
              labelText: t.t('documents.search'),
              suffixIcon: IconButton(
                onPressed: () => _reloadResources(),
                icon: const Icon(Icons.search),
              ),
            ),
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _reloadResources(),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _resourceSubjectController,
                  decoration: InputDecoration(
                    labelText: t.t('documents.subject'),
                  ),
                  onSubmitted: (_) => _reloadResources(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _resourceLevelController,
                  decoration: InputDecoration(
                    labelText: t.t('documents.level'),
                  ),
                  onSubmitted: (_) => _reloadResources(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ChoiceChip(
                label: Text(t.t('documents.allTypes')),
                selected: _selectedResourceType.isEmpty,
                onSelected: (_) {
                  setState(() => _selectedResourceType = '');
                  _reloadResources();
                },
              ),
              ..._resourceTypes.map(
                (type) => ChoiceChip(
                  label: Text(t.t('documents.resourceTypes.$type')),
                  selected: _selectedResourceType == type,
                  onSelected: (_) {
                    setState(() => _selectedResourceType = type);
                    _reloadResources();
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<double?>(
            initialValue: _resourceMinRating,
            decoration: InputDecoration(
              labelText: t.t('documents.minRating'),
            ),
            items: [
              DropdownMenuItem<double?>(
                value: null,
                child: Text(t.t('documents.all')),
              ),
              const DropdownMenuItem<double?>(value: 4, child: Text('4+')),
              const DropdownMenuItem<double?>(value: 3, child: Text('3+')),
            ],
            onChanged: (value) {
              setState(() => _resourceMinRating = value);
              _reloadResources();
            },
          ),
          if (_canUploadResources) ...[
            const SizedBox(height: 12),
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: OutlinedButton.icon(
                onPressed: _pickAndUploadResource,
                icon: const Icon(Icons.cloud_upload_outlined),
                label: Text(t.t('documents.uploadResource')),
              ),
            ),
          ],
          const SizedBox(height: 16),
          if (_resources.isEmpty)
            Center(child: Text(t.t('documents.resourcesEmpty')))
          else
            ..._resources.map(
              (resource) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _ResourceCard(
                  item: resource,
                  locale: ref.read(localeProvider),
                  onTap: () => _openResource(resource),
                  onDownload: () => _shareResource(resource),
                  onRate:
                      resource.canRate ? () => _rateResource(resource) : null,
                  onDelete: resource.canDelete
                      ? () => _deleteResource(resource)
                      : null,
                ),
              ),
            ),
          if (_resourcesHasMore) ...[
            const SizedBox(height: 8),
            FilledButton.tonal(
              onPressed: _loadingMoreResources ? null : _loadMoreResources,
              child: _loadingMoreResources
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(t.t('documents.loadMore')),
            ),
          ],
        ],
      ),
    );
  }
}

class _DocumentCard extends StatelessWidget {
  final ManagedDocument item;
  final String locale;
  final VoidCallback onTap;
  final VoidCallback onShare;
  final VoidCallback? onDelete;

  const _DocumentCard({
    required this.item,
    required this.locale,
    required this.onTap,
    required this.onShare,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(locale);
    final createdAt = _formatDate(item.createdAt, locale);
    final expiresAt =
        item.expiresAt == null ? null : _formatDate(item.expiresAt!, locale);

    return Card(
      child: ListTile(
        onTap: onTap,
        leading: _DocumentThumb(item: item),
        title: Text(
          item.originalFilename,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                _MetaChip(label: t.t('documents.categories.${item.category}')),
                _MetaChip(label: _humanSize(item.sizeBytes)),
                if (item.availableOffline)
                  _MetaChip(label: t.t('documents.offline')),
                if (item.deduplicated) const _MetaChip(label: 'SHA-256'),
                if (item.isExpired)
                  _MetaChip(
                    label: t.t('documents.status.expired'),
                    color: Colors.red,
                  ),
                if (item.isExpiringSoon)
                  _MetaChip(
                    label: t.t('documents.expiring'),
                    color: Colors.orange,
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(createdAt),
            if (item.linkedStudentName != null &&
                item.linkedStudentName!.isNotEmpty)
              Text(item.linkedStudentName!),
            if (expiresAt != null) Text(expiresAt),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) {
            switch (value) {
              case 'share':
                onShare();
                break;
              case 'delete':
                onDelete?.call();
                break;
            }
          },
          itemBuilder: (context) => [
            PopupMenuItem(
              value: 'share',
              child: Text(t.t('documents.share')),
            ),
            if (onDelete != null)
              PopupMenuItem(
                value: 'delete',
                child: Text(t.t('documents.delete')),
              ),
          ],
        ),
      ),
    );
  }
}

class _ChecklistCard extends StatelessWidget {
  final StudentDocumentChecklistItem item;
  final String locale;

  const _ChecklistCard({
    required this.item,
    required this.locale,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(locale);
    final color = switch (item.status) {
      'uploaded' => Colors.green,
      'expired' => Colors.red,
      _ => Colors.orange,
    };
    final expiresLabel =
        item.expiresAt == null ? null : _formatDate(item.expiresAt!, locale);

    return Card(
      child: ListTile(
        title: Text(t.t('documents.categories.${item.category}')),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (item.description != null && item.description!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(item.description!),
              ),
            if (item.document != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(item.document!.originalFilename),
              ),
            if (expiresLabel != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(expiresLabel),
              ),
          ],
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.14),
            borderRadius: BorderRadius.circular(999),
          ),
          child: Text(
            t.t('documents.status.${item.status}'),
            style: TextStyle(color: color, fontWeight: FontWeight.w600),
          ),
        ),
      ),
    );
  }
}

class _ResourceCard extends StatelessWidget {
  final ResourceLibraryItem item;
  final String locale;
  final VoidCallback onTap;
  final VoidCallback onDownload;
  final VoidCallback? onRate;
  final VoidCallback? onDelete;

  const _ResourceCard({
    required this.item,
    required this.locale,
    required this.onTap,
    required this.onDownload,
    this.onRate,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(locale);
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.title,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 6),
                        Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          children: [
                            if (item.subject != null &&
                                item.subject!.isNotEmpty)
                              _MetaChip(label: item.subject!),
                            if (item.level != null && item.level!.isNotEmpty)
                              _MetaChip(label: item.level!),
                            _MetaChip(
                              label:
                                  t.t('documents.resourceTypes.${item.type}'),
                            ),
                            if (item.availableOffline)
                              _MetaChip(label: t.t('documents.offline')),
                          ],
                        ),
                      ],
                    ),
                  ),
                  if (onDelete != null)
                    IconButton(
                      onPressed: onDelete,
                      icon: const Icon(Icons.delete_outline),
                    ),
                ],
              ),
              if (item.description != null && item.description!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(item.description!),
              ],
              const SizedBox(height: 12),
              Row(
                children: [
                  ...List.generate(
                    5,
                    (index) => Icon(
                      index < item.avgRating.round()
                          ? Icons.star
                          : Icons.star_border,
                      size: 18,
                      color: Colors.amber,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${item.avgRating.toStringAsFixed(1)} · ${item.ratingCount}',
                  ),
                  const Spacer(),
                  Text('${item.downloadCount}'),
                ],
              ),
              if (item.tags.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: item.tags
                      .take(4)
                      .map((tag) => _MetaChip(label: '#$tag'))
                      .toList(),
                ),
              ],
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: onTap,
                    icon: const Icon(Icons.visibility_outlined),
                    label: Text(t.t('documents.preview')),
                  ),
                  OutlinedButton.icon(
                    onPressed: onDownload,
                    icon: const Icon(Icons.download_outlined),
                    label: Text(t.t('documents.download')),
                  ),
                  if (onRate != null)
                    OutlinedButton.icon(
                      onPressed: onRate,
                      icon: const Icon(Icons.star_outline),
                      label: Text(t.t('documents.rate')),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DocumentThumb extends StatelessWidget {
  final ManagedDocument item;

  const _DocumentThumb({required this.item});

  @override
  Widget build(BuildContext context) {
    if (item.isImage &&
        item.thumbnailUrl != null &&
        item.thumbnailUrl!.isNotEmpty) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(10),
        child: Image.network(
          'http://localhost:8000${item.thumbnailUrl!}',
          width: 52,
          height: 52,
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) {
            return _fallback();
          },
        ),
      );
    }
    return _fallback();
  }

  Widget _fallback() {
    return Container(
      width: 52,
      height: 52,
      decoration: BoxDecoration(
        color: Colors.blueGrey.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
      ),
      alignment: Alignment.center,
      child: Icon(
        item.isPdf
            ? Icons.picture_as_pdf_outlined
            : item.isImage
                ? Icons.image_outlined
                : Icons.insert_drive_file_outlined,
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  final String label;
  final Color? color;

  const _MetaChip({
    required this.label,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final background = (color ?? Colors.blueGrey).withValues(alpha: 0.12);
    final foreground = color ?? Colors.blueGrey.shade700;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: foreground,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _CategoryChipBar extends StatelessWidget {
  final List<String> categories;
  final String selected;
  final ValueChanged<String> onChanged;

  const _CategoryChipBar({
    required this.categories,
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(Localizations.localeOf(context).languageCode);
    final allCategories = categories.isEmpty ? const ['other'] : categories;
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        ChoiceChip(
          label: Text(t.t('documents.all')),
          selected: selected.isEmpty,
          onSelected: (_) => onChanged(''),
        ),
        ...allCategories.map(
          (category) => ChoiceChip(
            label: Text(t.t('documents.categories.$category')),
            selected: selected == category,
            onSelected: (_) => onChanged(category),
          ),
        ),
      ],
    );
  }
}

class _ErrorCard extends StatelessWidget {
  final String message;

  const _ErrorCard({required this.message});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.red.shade50,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Text(
          message,
          style: const TextStyle(color: Colors.red),
        ),
      ),
    );
  }
}

class _UploadProgressCard extends StatelessWidget {
  final String title;
  final double progress;

  const _UploadProgressCard({
    required this.title,
    required this.progress,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title),
            const SizedBox(height: 8),
            LinearProgressIndicator(value: progress.clamp(0, 1)),
            const SizedBox(height: 8),
            Text('${(progress * 100).round()}%'),
          ],
        ),
      ),
    );
  }
}

class _ResourceUploadPayload {
  final String title;
  final String description;
  final String subject;
  final String level;
  final String type;
  final List<String> tags;

  const _ResourceUploadPayload({
    required this.title,
    required this.description,
    required this.subject,
    required this.level,
    required this.type,
    required this.tags,
  });
}

String _humanSize(int bytes) {
  if (bytes < 1024) return '$bytes B';
  if (bytes < 1024 * 1024) {
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  }
  return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
}

String _formatDate(String value, String locale) {
  try {
    final parsed = DateTime.parse(value).toLocal();
    return DateFormat.yMMMd(locale).add_Hm().format(parsed);
  } catch (_) {
    return value;
  }
}
