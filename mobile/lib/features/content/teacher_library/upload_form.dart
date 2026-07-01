part of 'content_library_screen.dart';

// Scanning state is inferred from upload progress:
//   progress < 1.0 → uploading
//   progress == 1.0 while still pending → backend scanning / processing

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
      allowedExtensions: [
        'pdf',
        'doc',
        'docx',
        'mp4',
        'mp3',
        'wav',
        'jpg',
        'png',
      ],
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
      final schoolId = ref.read(authProvider).user?.schoolId ?? '';
      await repo.uploadContent(
        title: _titleController.text.trim(),
        contentType: _contentType,
        schoolId: schoolId,
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
    return UploadForm(
      titleController: _titleController,
      descriptionController: _descriptionController,
      contentType: _contentType,
      language: _language,
      level: _level,
      subject: _subject,
      fileName: _fileName,
      uploading: _uploading,
      uploadProgress: _uploadProgress,
      error: _error,
      success: _success,
      onContentTypeChanged: (value) => setState(() => _contentType = value),
      onLanguageChanged: (value) => setState(() => _language = value),
      onLevelChanged: (value) => setState(() => _level = value),
      onSubjectChanged: (value) => setState(() => _subject = value),
      onPickFile: _pickFile,
      onPickCamera: _pickFromCamera,
      onPickGallery: _pickFromGallery,
      onClearFile: () => setState(() {
        _selectedFile = null;
        _fileName = null;
      }),
      onDismissError: () => setState(() => _error = null),
      onSubmit: _upload,
    );
  }
}

class UploadForm extends ConsumerWidget {
  final TextEditingController titleController;
  final TextEditingController descriptionController;
  final String contentType;
  final String language;
  final String? level;
  final String? subject;
  final String? fileName;
  final bool uploading;
  final double uploadProgress;
  final String? error;
  final String? success;
  final ValueChanged<String> onContentTypeChanged;
  final ValueChanged<String> onLanguageChanged;
  final ValueChanged<String?> onLevelChanged;
  final ValueChanged<String?> onSubjectChanged;
  final VoidCallback onPickFile;
  final VoidCallback onPickCamera;
  final VoidCallback onPickGallery;
  final VoidCallback onClearFile;
  final VoidCallback onDismissError;
  final VoidCallback onSubmit;

  const UploadForm({
    super.key,
    required this.titleController,
    required this.descriptionController,
    required this.contentType,
    required this.language,
    required this.level,
    required this.subject,
    required this.fileName,
    required this.uploading,
    required this.uploadProgress,
    required this.error,
    required this.success,
    required this.onContentTypeChanged,
    required this.onLanguageChanged,
    required this.onLevelChanged,
    required this.onSubjectChanged,
    required this.onPickFile,
    required this.onPickCamera,
    required this.onPickGallery,
    required this.onClearFile,
    required this.onDismissError,
    required this.onSubmit,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);

    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        if (error != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.errorContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.error_outline,
                  color: theme.colorScheme.error,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    error!,
                    style: TextStyle(color: theme.colorScheme.onErrorContainer),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 18),
                  onPressed: onDismissError,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],
        if (success != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.semanticPalette.successContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.check_circle,
                  color: theme.semanticPalette.success,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    success!,
                    style: TextStyle(color: theme.semanticPalette.success),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],
        TextFormField(
          controller: titleController,
          decoration: InputDecoration(
            labelText: t.t('upload.titleLabel'),
            border: const OutlineInputBorder(),
          ),
          enabled: !uploading,
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: descriptionController,
          maxLines: 3,
          decoration: InputDecoration(
            labelText: t.t('contentLibrary.uploadDescription'),
            border: const OutlineInputBorder(),
            alignLabelWithHint: true,
          ),
          enabled: !uploading,
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          initialValue: contentType,
          decoration: InputDecoration(
            labelText: t.t('contentLibrary.uploadType'),
            border: const OutlineInputBorder(),
          ),
          items: [
            DropdownMenuItem(
              value: 'DOCUMENT',
              child: Text(t.t('upload.typeDocument')),
            ),
            DropdownMenuItem(
              value: 'VIDEO',
              child: Text(t.t('upload.typeVideo')),
            ),
            DropdownMenuItem(
              value: 'AUDIO',
              child: Text(t.t('upload.typeAudio')),
            ),
            DropdownMenuItem(
              value: 'INTERACTIVE',
              child: Text(t.t('upload.typeInteractive')),
            ),
          ],
          onChanged: uploading
              ? null
              : (value) {
                  if (value != null) onContentTypeChanged(value);
                },
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          initialValue: language,
          decoration: InputDecoration(
            labelText: t.t('contentLibrary.uploadLanguage'),
            border: const OutlineInputBorder(),
          ),
          items: const [
            DropdownMenuItem(value: 'fr', child: Text('Français')),
            DropdownMenuItem(value: 'ar', child: Text('العربية')),
            DropdownMenuItem(value: 'en', child: Text('English')),
          ],
          onChanged: uploading
              ? null
              : (value) {
                  if (value != null) onLanguageChanged(value);
                },
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String?>(
          initialValue: level,
          decoration: InputDecoration(
            labelText: t.t('content.filter.level'),
            border: const OutlineInputBorder(),
          ),
          items: [
            DropdownMenuItem<String?>(
              value: null,
              child: Text(t.t('profileForm.select')),
            ),
            ...Taxonomy.levelBands.map(
              (level) => DropdownMenuItem<String?>(
                value: level,
                child: Text(level),
              ),
            ),
          ],
          onChanged: uploading ? null : onLevelChanged,
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String?>(
          initialValue: subject,
          decoration: InputDecoration(
            labelText: t.t('common.subject'),
            border: const OutlineInputBorder(),
          ),
          items: [
            DropdownMenuItem<String?>(
              value: null,
              child: Text(t.t('profileForm.select')),
            ),
            ...Taxonomy.subjects.map(
              (subject) => DropdownMenuItem<String?>(
                value: subject,
                child: Text(_subjectLabel(subject, t.locale)),
              ),
            ),
          ],
          onChanged: uploading ? null : onSubjectChanged,
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Fichier *',
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _PickerBtn(
                      icon: Icons.folder_open,
                      label: 'Fichier',
                      onTap: uploading ? null : onPickFile,
                    ),
                    const SizedBox(width: 12),
                    _PickerBtn(
                      icon: Icons.camera_alt_outlined,
                      label: 'Caméra',
                      onTap: uploading ? null : onPickCamera,
                    ),
                    const SizedBox(width: 12),
                    _PickerBtn(
                      icon: Icons.photo_library_outlined,
                      label: 'Galerie',
                      onTap: uploading ? null : onPickGallery,
                    ),
                  ],
                ),
                if (fileName != null) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.attach_file, size: 18),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          fileName!,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: uploading ? null : onClearFile,
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        if (uploading) ...[
          // progress < 1.0 → uploading phase with determinate bar.
          // progress == 1.0 → PUT complete, backend scanning (indeterminate).
          uploadProgress < 1.0
              ? LinearProgressIndicator(value: uploadProgress)
              : const LinearProgressIndicator(),
          const SizedBox(height: 8),
          Text(
            uploadProgress < 1.0
                ? 'Envoi... ${(uploadProgress * 100).toStringAsFixed(0)}%'
                : 'Analyse en cours…',
            style: theme.textTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
        ],
        FilledButton.icon(
          onPressed: uploading ? null : onSubmit,
          icon: uploading
              ? SizedBox(
                  height: 16,
                  width: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: theme.colorScheme.onPrimary,
                  ),
                )
              : const Icon(Icons.upload),
          label: Text(
            uploading
                ? (uploadProgress < 1.0 ? 'Envoi en cours...' : 'Analyse…')
                : 'Téléverser',
          ),
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
        ),
      ],
    );
  }

  String _subjectLabel(String code, String locale) {
    final titles = Taxonomy.subjectTitles[code];
    return titles?[locale] ?? titles?['fr'] ?? code;
  }
}

class _PickerBtn extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  const _PickerBtn({
    required this.icon,
    required this.label,
    this.onTap,
  });

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
