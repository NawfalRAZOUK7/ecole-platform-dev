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
    state = _LibraryState(typeFilter: v, levelFilter: state.levelFilter, originFilter: state.originFilter);
    load();
  }

  void setLevelFilter(String? v) {
    state = _LibraryState(typeFilter: state.typeFilter, levelFilter: v, originFilter: state.originFilter);
    load();
  }

  void setOriginFilter(String? v) {
    state = _LibraryState(typeFilter: state.typeFilter, levelFilter: state.levelFilter, originFilter: v);
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

// ── Browse Tab ──

class _BrowseTab extends ConsumerWidget {
  const _BrowseTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(_libraryProvider);
    final theme = Theme.of(context);

    return Column(
      children: [
        // Filters
        SearchFilterBar(
          searchHint: 'Rechercher du contenu...',
          searchValue: '',
          onSearchChanged: (_) {},
          filters: {
            'Type': const [
              FilterOption(label: 'Tous', value: null),
              FilterOption(label: 'Vidéo', value: 'VIDEO'),
              FilterOption(label: 'Audio', value: 'AUDIO'),
              FilterOption(label: 'Document', value: 'DOCUMENT'),
              FilterOption(label: 'Interactif', value: 'INTERACTIVE'),
            ],
            'Origine': const [
              FilterOption(label: 'Tous', value: null),
              FilterOption(label: 'Plateforme', value: 'platform'),
              FilterOption(label: 'École', value: 'school'),
            ],
          },
          filterValues: {
            'Type': state.typeFilter,
            'Origine': state.originFilter,
          },
          onFilterChanged: (key, value) {
            if (key == 'Type') {
              ref.read(_libraryProvider.notifier).setTypeFilter(value);
            } else {
              ref.read(_libraryProvider.notifier).setOriginFilter(value);
            }
          },
        ),

        // Content list
        Expanded(child: _buildBrowseList(context, ref, state, theme)),
      ],
    );
  }

  Widget _buildBrowseList(
      BuildContext context, WidgetRef ref, _LibraryState state, ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(_libraryProvider.notifier).load(),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      );
    }
    if (state.items.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.library_books, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('Aucun contenu disponible'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(_libraryProvider.notifier).load(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length,
        itemBuilder: (context, index) {
          final item = state.items[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: _typeColor(item.contentType).withAlpha(30),
                child: Icon(_typeIcon(item.contentType),
                    color: _typeColor(item.contentType)),
              ),
              title: Text(item.title,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Row(
                children: [
                  Chip(
                    label: Text(item.contentType,
                        style: const TextStyle(fontSize: 10)),
                    padding: EdgeInsets.zero,
                    visualDensity: VisualDensity.compact,
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  const SizedBox(width: 4),
                  Chip(
                    label: Text(
                      item.origin == 'platform' ? 'Plateforme' : 'École',
                      style: TextStyle(
                        fontSize: 10,
                        color: item.origin == 'platform'
                            ? Colors.blue
                            : Colors.green,
                      ),
                    ),
                    padding: EdgeInsets.zero,
                    visualDensity: VisualDensity.compact,
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                ],
              ),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Assign to class
                  IconButton(
                    icon: const Icon(Icons.assignment_add, size: 20),
                    tooltip: 'Assigner à une classe',
                    onPressed: () => _showAssignDialog(context, ref, item),
                  ),
                  // Submit for review (school content only)
                  if (item.origin == 'school')
                    IconButton(
                      icon: const Icon(Icons.publish, size: 20),
                      tooltip: 'Soumettre pour révision',
                      onPressed: () => _submitForReview(context, ref, item.id),
                    ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Future<void> _showAssignDialog(
      BuildContext context, WidgetRef ref, LibraryItem item) async {
    final repo = ref.read(contentLibraryRepositoryProvider);
    List<ClassInfo>? classes;
    try {
      classes = await repo.getTeacherClasses();
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
        );
      }
      return;
    }

    if (!context.mounted || classes == null || classes.isEmpty) return;

    final selectedClass = await showDialog<ClassInfo>(
      context: context,
      builder: (ctx) => SimpleDialog(
        title: Text('Assigner "${item.title}"'),
        children: classes!.map((c) => SimpleDialogOption(
          onPressed: () => Navigator.pop(ctx, c),
          child: ListTile(
            title: Text(c.name),
            subtitle: Text('${c.studentCount} élèves'),
            leading: const Icon(Icons.class_),
          ),
        )).toList(),
      ),
    );

    if (selectedClass == null || !context.mounted) return;

    try {
      await repo.assignContent(
        contentItemId: item.id,
        classId: selectedClass.id,
      );
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Contenu assigné à ${selectedClass.name}'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _submitForReview(
      BuildContext context, WidgetRef ref, String contentId) async {
    try {
      await ref.read(contentLibraryRepositoryProvider).submitForReview(contentId);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Soumis pour révision'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  IconData _typeIcon(String type) {
    switch (type.toUpperCase()) {
      case 'VIDEO':
        return Icons.play_circle_outline;
      case 'AUDIO':
        return Icons.audiotrack;
      case 'DOCUMENT':
        return Icons.description;
      case 'INTERACTIVE':
        return Icons.touch_app;
      default:
        return Icons.article;
    }
  }

  Color _typeColor(String type) {
    switch (type.toUpperCase()) {
      case 'VIDEO':
        return Colors.red;
      case 'AUDIO':
        return Colors.purple;
      case 'DOCUMENT':
        return Colors.blue;
      case 'INTERACTIVE':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}

// ── Upload Tab ──

class _UploadTab extends ConsumerStatefulWidget {
  const _UploadTab();

  @override
  ConsumerState<_UploadTab> createState() => _UploadTabState();
}

class _UploadTabState extends ConsumerState<_UploadTab> {
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  String _contentType = 'DOCUMENT';
  String? _level;
  String? _subject;
  String _language = 'fr';
  File? _selectedFile;
  String? _fileName;
  bool _uploading = false;
  double _uploadProgress = 0;
  String? _error;
  String? _success;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'doc', 'docx', 'mp4', 'mp3', 'wav', 'jpg', 'png'],
    );
    if (result != null && result.files.single.path != null) {
      setState(() {
        _selectedFile = File(result.files.single.path!);
        _fileName = result.files.single.name;
      });
    }
  }

  Future<void> _pickFromCamera() async {
    final picker = ImagePicker();
    final photo = await picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 2048,
      maxHeight: 2048,
      imageQuality: 85,
    );
    if (photo != null) {
      setState(() {
        _selectedFile = File(photo.path);
        _fileName = photo.name;
      });
    }
  }

  Future<void> _pickFromGallery() async {
    final picker = ImagePicker();
    final image = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 2048,
      maxHeight: 2048,
      imageQuality: 85,
    );
    if (image != null) {
      setState(() {
        _selectedFile = File(image.path);
        _fileName = image.name;
      });
    }
  }

  Future<void> _upload() async {
    if (_titleController.text.trim().isEmpty) {
      setState(() => _error = 'Le titre est requis');
      return;
    }
    if (_selectedFile == null) {
      setState(() => _error = 'Veuillez sélectionner un fichier');
      return;
    }

    setState(() {
      _uploading = true;
      _uploadProgress = 0;
      _error = null;
      _success = null;
    });

    try {
      final repo = ref.read(contentLibraryRepositoryProvider);
      await repo.uploadContent(
        title: _titleController.text.trim(),
        contentType: _contentType,
        description: _descriptionController.text.trim().isNotEmpty
            ? _descriptionController.text.trim()
            : null,
        level: _level,
        subject: _subject,
        language: _language,
        file: _selectedFile!,
        onProgress: (sent, total) {
          if (total > 0) {
            setState(() => _uploadProgress = sent / total);
          }
        },
      );
      setState(() {
        _success = 'Contenu téléversé avec succès';
        _titleController.clear();
        _descriptionController.clear();
        _selectedFile = null;
        _fileName = null;
      });
    } catch (e) {
      setState(() => _error = 'Erreur: $e');
    } finally {
      setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        // Error
        if (_error != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.errorContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(Icons.error_outline, color: theme.colorScheme.error, size: 20),
                const SizedBox(width: 8),
                Expanded(child: Text(_error!, style: TextStyle(color: theme.colorScheme.onErrorContainer))),
                IconButton(
                  icon: const Icon(Icons.close, size: 18),
                  onPressed: () => setState(() => _error = null),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],

        // Success
        if (_success != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.green, size: 20),
                const SizedBox(width: 8),
                Expanded(child: Text(_success!, style: const TextStyle(color: Colors.green))),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],

        // Title
        TextFormField(
          controller: _titleController,
          decoration: const InputDecoration(
            labelText: 'Titre *',
            border: OutlineInputBorder(),
          ),
          enabled: !_uploading,
        ),
        const SizedBox(height: 16),

        // Description
        TextFormField(
          controller: _descriptionController,
          maxLines: 3,
          decoration: const InputDecoration(
            labelText: 'Description',
            border: OutlineInputBorder(),
            alignLabelWithHint: true,
          ),
          enabled: !_uploading,
        ),
        const SizedBox(height: 16),

        // Content type dropdown
        DropdownButtonFormField<String>(
          value: _contentType,
          decoration: const InputDecoration(
            labelText: 'Type de contenu',
            border: OutlineInputBorder(),
          ),
          items: const [
            DropdownMenuItem(value: 'DOCUMENT', child: Text('Document (PDF)')),
            DropdownMenuItem(value: 'VIDEO', child: Text('Vidéo')),
            DropdownMenuItem(value: 'AUDIO', child: Text('Audio')),
            DropdownMenuItem(value: 'INTERACTIVE', child: Text('Interactif')),
          ],
          onChanged: _uploading ? null : (v) => setState(() => _contentType = v!),
        ),
        const SizedBox(height: 16),

        // Language
        DropdownButtonFormField<String>(
          value: _language,
          decoration: const InputDecoration(
            labelText: 'Langue',
            border: OutlineInputBorder(),
          ),
          items: const [
            DropdownMenuItem(value: 'fr', child: Text('Français')),
            DropdownMenuItem(value: 'ar', child: Text('العربية')),
            DropdownMenuItem(value: 'en', child: Text('English')),
          ],
          onChanged: _uploading ? null : (v) => setState(() => _language = v!),
        ),
        const SizedBox(height: 16),

        // File picker buttons
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Fichier *', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _PickerBtn(
                      icon: Icons.folder_open,
                      label: 'Fichier',
                      onTap: _uploading ? null : _pickFile,
                    ),
                    const SizedBox(width: 12),
                    _PickerBtn(
                      icon: Icons.camera_alt_outlined,
                      label: 'Caméra',
                      onTap: _uploading ? null : _pickFromCamera,
                    ),
                    const SizedBox(width: 12),
                    _PickerBtn(
                      icon: Icons.photo_library_outlined,
                      label: 'Galerie',
                      onTap: _uploading ? null : _pickFromGallery,
                    ),
                  ],
                ),
                if (_fileName != null) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.attach_file, size: 18),
                      const SizedBox(width: 4),
                      Expanded(child: Text(_fileName!, overflow: TextOverflow.ellipsis)),
                      IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: _uploading
                            ? null
                            : () => setState(() {
                                  _selectedFile = null;
                                  _fileName = null;
                                }),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),

        // Upload progress
        if (_uploading) ...[
          LinearProgressIndicator(value: _uploadProgress),
          const SizedBox(height: 8),
          Text(
            'Envoi... ${(_uploadProgress * 100).toStringAsFixed(0)}%',
            style: theme.textTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
        ],

        // Submit button
        FilledButton.icon(
          onPressed: _uploading ? null : _upload,
          icon: _uploading
              ? const SizedBox(
                  height: 16, width: 16,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Icon(Icons.upload),
          label: Text(_uploading ? 'Envoi en cours...' : 'Téléverser'),
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
        ),
      ],
    );
  }
}

class _PickerBtn extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  const _PickerBtn({required this.icon, required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(
            border: Border.all(color: theme.colorScheme.outline),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Icon(icon, size: 28, color: theme.colorScheme.primary),
              const SizedBox(height: 4),
              Text(label, style: theme.textTheme.labelSmall),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Submissions Tab ──

class _SubmissionsTab extends ConsumerStatefulWidget {
  const _SubmissionsTab();

  @override
  ConsumerState<_SubmissionsTab> createState() => _SubmissionsTabState();
}

class _SubmissionsTabState extends ConsumerState<_SubmissionsTab> {
  List<ContentSubmission> _submissions = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = ref.read(contentLibraryRepositoryProvider);
      _submissions = await repo.getMySubmissions();
      setState(() => _loading = false);
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(_error!),
            const SizedBox(height: 16),
            FilledButton.tonal(onPressed: _fetch, child: const Text('Réessayer')),
          ],
        ),
      );
    }
    if (_submissions.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('Aucune soumission'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetch,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _submissions.length,
        itemBuilder: (context, index) {
          final s = _submissions[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              title: Text(s.contentTitle,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  _StatusBadge(status: s.status),
                  if (s.reviewNotes != null) ...[
                    const SizedBox(height: 4),
                    Text(s.reviewNotes!,
                        style: theme.textTheme.bodySmall?.copyWith(
                          fontStyle: FontStyle.italic,
                        )),
                  ],
                ],
              ),
              trailing: s.submittedAt != null
                  ? Text(
                      s.submittedAt!.substring(0, 10),
                      style: theme.textTheme.bodySmall,
                    )
                  : null,
            ),
          );
        },
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (status.toLowerCase()) {
      'pending' => (Colors.orange, 'En attente'),
      'approved' => (Colors.green, 'Approuvé'),
      'rejected' => (Colors.red, 'Rejeté'),
      'promoted' => (Colors.blue, 'Promu'),
      _ => (Colors.grey, status),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color),
      ),
      child: Text(label, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w600)),
    );
  }
}
