part of 'documents_screen.dart';

extension _DocumentsActions on _DocumentsScreenState {
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

    _applyState(() {
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
              _applyState(() {
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
          content: Text(AppLocalizations.of(ref).t('documents.uploadSuccess')),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _applyState(() => _error = e.toString());
    } finally {
      if (!mounted) return;
      _applyState(() {
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

    _applyState(() {
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
              _applyState(() => _uploadProgress = sent / total);
            },
          );
      if (!mounted) return;
      await _reloadResources();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content:
              Text(AppLocalizations.of(ref).t('documents.resourceUploaded')),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _applyState(() => _error = e.toString());
    } finally {
      if (!mounted) return;
      _applyState(() {
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

  Future<void> _deleteDocument(
    ManagedDocument document, {
    bool hardDelete = false,
  }) async {
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
      _applyState(() {
        _resources = _resources
            .map(
              (item) => item.id == resource.id
                  ? item.copyWith(
                      myRating: summary.myRating ?? rating,
                      avgRating: summary.avgRating,
                      ratingCount: summary.ratingCount,
                    )
                  : item,
            )
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
          builder: (dialogContext) => AlertDialog(
            title: Text(t.t('documents.delete')),
            content: Text(t.t('documents.confirmDelete')),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(dialogContext).pop(false),
                child: Text(t.t('common.cancel')),
              ),
              FilledButton(
                onPressed: () => Navigator.of(dialogContext).pop(true),
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
      builder: (modalContext) {
        return StatefulBuilder(
          builder: (modalContext, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(modalContext).viewInsets.bottom + 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    t.t('documents.uploadMetadata'),
                    style: Theme.of(modalContext).textTheme.titleMedium,
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
                        context: modalContext,
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
                        Navigator.of(modalContext).pop(
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
      builder: (modalContext) {
        return StatefulBuilder(
          builder: (modalContext, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(modalContext).viewInsets.bottom + 20,
              ),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      t.t('documents.resourceUpload'),
                      style: Theme.of(modalContext).textTheme.titleMedium,
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
                          Navigator.of(modalContext).pop(
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
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
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
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: Text(t.t('common.cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(selectedRating),
              child: Text(t.t('documents.save')),
            ),
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
