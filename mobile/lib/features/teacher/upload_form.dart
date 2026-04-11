part of 'content_library_screen.dart';

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
    return UploadForm(
      titleController: _titleController,
      descriptionController: _descriptionController,
      contentType: _contentType,
      language: _language,
      fileName: _fileName,
      uploading: _uploading,
      uploadProgress: _uploadProgress,
      error: _error,
      success: _success,
      onContentTypeChanged: (value) => setState(() => _contentType = value),
      onLanguageChanged: (value) => setState(() => _language = value),
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

class UploadForm extends StatelessWidget {
  final TextEditingController titleController;
  final TextEditingController descriptionController;
  final String contentType;
  final String language;
  final String? fileName;
  final bool uploading;
  final double uploadProgress;
  final String? error;
  final String? success;
  final ValueChanged<String> onContentTypeChanged;
  final ValueChanged<String> onLanguageChanged;
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
    required this.fileName,
    required this.uploading,
    required this.uploadProgress,
    required this.error,
    required this.success,
    required this.onContentTypeChanged,
    required this.onLanguageChanged,
    required this.onPickFile,
    required this.onPickCamera,
    required this.onPickGallery,
    required this.onClearFile,
    required this.onDismissError,
    required this.onSubmit,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

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
                Icon(Icons.error_outline,
                    color: theme.colorScheme.error, size: 20),
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
                Icon(Icons.check_circle,
                    color: theme.semanticPalette.success, size: 20),
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
          decoration: const InputDecoration(
            labelText: 'Titre *',
            border: OutlineInputBorder(),
          ),
          enabled: !uploading,
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: descriptionController,
          maxLines: 3,
          decoration: const InputDecoration(
            labelText: 'Description',
            border: OutlineInputBorder(),
            alignLabelWithHint: true,
          ),
          enabled: !uploading,
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          initialValue: contentType,
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
          onChanged: uploading
              ? null
              : (value) {
                  if (value != null) onContentTypeChanged(value);
                },
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          initialValue: language,
          decoration: const InputDecoration(
            labelText: 'Langue',
            border: OutlineInputBorder(),
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
          LinearProgressIndicator(value: uploadProgress),
          const SizedBox(height: 8),
          Text(
            'Envoi... ${(uploadProgress * 100).toStringAsFixed(0)}%',
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
          label: Text(uploading ? 'Envoi en cours...' : 'Téléverser'),
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
        ),
      ],
    );
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
