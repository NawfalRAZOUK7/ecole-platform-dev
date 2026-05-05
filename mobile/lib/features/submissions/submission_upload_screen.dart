/// Submission upload screen — file picker (gallery, camera, documents) + progress.
///
/// Reference: Phase 5A (from 3B) — File picker for submission upload
/// Allows students to pick files from gallery, camera, or documents,
/// preview selected files, and upload with progress indicator.
/// Phase 10C: Added PDF exercise download + camera capture for PRINTABLE_PDF assignments.

import 'dart:developer' as dev;
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/data/services/upload_client.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

/// Represents a file selected for upload.
class _SelectedFile {
  final String name;
  final String path;
  final int sizeBytes;
  final String? mimeType;

  const _SelectedFile({
    required this.name,
    required this.path,
    required this.sizeBytes,
    this.mimeType,
  });

  String get sizeLabel {
    if (sizeBytes < 1024) return '$sizeBytes B';
    if (sizeBytes < 1024 * 1024)
      return '${(sizeBytes / 1024).toStringAsFixed(1)} KB';
    return '${(sizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  bool get isImage {
    final ext = name.toLowerCase();
    return ext.endsWith('.jpg') ||
        ext.endsWith('.jpeg') ||
        ext.endsWith('.png') ||
        ext.endsWith('.gif') ||
        ext.endsWith('.webp');
  }
}

class SubmissionUploadScreen extends ConsumerStatefulWidget {
  final String? assignmentId;
  final String? assignmentTitle;

  /// Phase 10C: exercise type (e.g. 'PRINTABLE_PDF')
  final String? exerciseType;

  /// Phase 10C: whether exercise PDF is available for download
  final bool hasExercisePdf;

  const SubmissionUploadScreen({
    super.key,
    this.assignmentId,
    this.assignmentTitle,
    this.exerciseType,
    this.hasExercisePdf = false,
  });

  @override
  ConsumerState<SubmissionUploadScreen> createState() =>
      _SubmissionUploadScreenState();
}

class _SubmissionUploadScreenState
    extends ConsumerState<SubmissionUploadScreen> {
  final List<_SelectedFile> _files = [];
  final _commentController = TextEditingController();
  bool _uploading = false;
  double _uploadProgress = 0;
  String? _error;

  // Files up to this limit use the legacy multipart path; larger files are
  // routed to direct-to-MinIO upload (handled in _upload).
  static const _legacyMaxFileSize = 50 * 1024 * 1024; // 50 MB per file
  static const _maxFiles = 5;
  bool _downloadingPdf = false;

  /// Phase 10C: Whether this is a PRINTABLE_PDF assignment.
  bool get _isPrintablePdf =>
      widget.exerciseType?.toUpperCase() == 'PRINTABLE_PDF';

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _pickFromGallery() async {
    try {
      final picker = ImagePicker();
      final image = await picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 2048,
        maxHeight: 2048,
        imageQuality: 85,
      );
      if (image == null) return;

      final file = File(image.path);
      final size = await file.length();
      _addFile(_SelectedFile(
        name: image.name,
        path: image.path,
        sizeBytes: size,
        mimeType: 'image/${image.name.split('.').last}',
      ));
    } catch (e) {
      setState(() => _error = 'Erreur lors de la sélection: $e');
    }
  }

  Future<void> _pickFromCamera() async {
    try {
      final picker = ImagePicker();
      final photo = await picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 2048,
        maxHeight: 2048,
        imageQuality: 85,
      );
      if (photo == null) return;

      final file = File(photo.path);
      final size = await file.length();
      _addFile(_SelectedFile(
        name: photo.name,
        path: photo.path,
        sizeBytes: size,
        mimeType: 'image/${photo.name.split('.').last}',
      ));
    } catch (e) {
      setState(() => _error = 'Erreur lors de la capture: $e');
    }
  }

  Future<void> _pickDocuments() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        allowMultiple: true,
        type: FileType.custom,
        allowedExtensions: [
          'pdf',
          'doc',
          'docx',
          'xls',
          'xlsx',
          'txt',
          'jpg',
          'jpeg',
          'png'
        ],
      );
      if (result == null) return;

      for (final file in result.files) {
        if (file.path == null) continue;
        _addFile(_SelectedFile(
          name: file.name,
          path: file.path!,
          sizeBytes: file.size,
          mimeType:
              file.extension != null ? _mimeFromExt(file.extension!) : null,
        ));
      }
    } catch (e) {
      setState(() => _error = 'Erreur lors de la sélection: $e');
    }
  }

  String _mimeFromExt(String ext) {
    switch (ext.toLowerCase()) {
      case 'pdf':
        return 'application/pdf';
      case 'doc':
      case 'docx':
        return 'application/msword';
      case 'xls':
      case 'xlsx':
        return 'application/vnd.ms-excel';
      case 'txt':
        return 'text/plain';
      case 'jpg':
      case 'jpeg':
        return 'image/jpeg';
      case 'png':
        return 'image/png';
      default:
        return 'application/octet-stream';
    }
  }

  void _addFile(_SelectedFile file) {
    if (_files.length >= _maxFiles) {
      setState(() => _error = 'Maximum $_maxFiles fichiers autorisés');
      return;
    }
    if (file.sizeBytes > _legacyMaxFileSize) {
      setState(
          () => _error = '${file.name} dépasse la taille maximale (50 MB)');
      return;
    }
    setState(() {
      _files.add(file);
      _error = null;
    });
  }

  void _removeFile(int index) {
    setState(() => _files.removeAt(index));
  }

  /// Phase 10C: Download exercise PDF for PRINTABLE_PDF assignments.
  Future<void> _downloadExercisePdf() async {
    if (widget.assignmentId == null) return;
    setState(() => _downloadingPdf = true);
    try {
      final dir = await getTemporaryDirectory();
      final savePath = '${dir.path}/exercise-${widget.assignmentId}.pdf';
      final file = await ref.read(signedUrlCacheProvider).download(
            '/assignments/${widget.assignmentId}/exercise-pdf',
            savePath: savePath,
          );
      final result = await OpenFilex.open(file.path);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.type == ResultType.done
                ? 'PDF de l\'exercice téléchargé'
                : result.message),
            backgroundColor: result.type == ResultType.done
                ? Theme.of(context).semanticPalette.success
                : Theme.of(context).colorScheme.error,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = 'Erreur de téléchargement: $e');
      }
    } finally {
      if (mounted) setState(() => _downloadingPdf = false);
    }
  }

  Future<void> _upload() async {
    if (_files.isEmpty) {
      setState(() => _error = 'Veuillez sélectionner au moins un fichier');
      return;
    }

    setState(() {
      _uploading = true;
      _uploadProgress = 0;
      _error = null;
    });

    try {
      final api = ref.read(apiClientProvider);

      // Single large file → direct-to-MinIO path.
      // Multiple files or small files → legacy multipart path.
      final isSingleLargeFile = _files.length == 1 &&
          shouldUseDirect(
            File(_files.first.path),
            UploadKind.submissionFile,
          );

      if (isSingleLargeFile) {
        final schoolId = ref.read(authProvider).user?.schoolId ?? '';
        await directUpload(
          api: api,
          kind: UploadKind.submissionFile,
          scope: UploadScope(
            schoolId: schoolId,
            submissionId: widget.assignmentId,
          ),
          file: File(_files.first.path),
          onProgress: (sent, total) {
            if (total > 0) {
              setState(() => _uploadProgress = sent / total);
            }
          },
        );
      } else {
        // Build multipart form data
        final formFields = <String, dynamic>{};
        if (widget.assignmentId != null) {
          formFields['assignment_id'] = widget.assignmentId;
        }
        if (_commentController.text.trim().isNotEmpty) {
          formFields['comment'] = _commentController.text.trim();
        }

        // Upload with progress tracking
        await api.uploadFiles(
          '/submissions/upload',
          files: _files.map((f) => File(f.path)).toList(),
          fields: formFields,
          onProgress: (sent, total) {
            if (total > 0) {
              setState(() => _uploadProgress = sent / total);
            }
          },
        );
      }

      // Phase 10C: finalize PRINTABLE_PDF submission
      if (_isPrintablePdf && widget.assignmentId != null) {
        try {
          await api.post('/submissions/finalize', body: {
            'assignment_id': widget.assignmentId,
          });
        } catch (_) {
          // Non-critical — submission was already uploaded
        }
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Devoir soumis avec succès'),
            backgroundColor: Theme.of(context).semanticPalette.success,
          ),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      dev.log('Upload error: $e', name: 'SubmissionUpload');
      setState(() => _error = 'Erreur lors de l\'envoi: $e');
    } finally {
      if (mounted) {
        setState(() => _uploading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.assignmentTitle ?? 'Soumettre un devoir'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // Error banner
          if (_error != null) ...[
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
                    child: Text(_error!,
                        style: TextStyle(
                            color: theme.colorScheme.onErrorContainer)),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => setState(() => _error = null),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Phase 10C: PDF exercise download section for PRINTABLE_PDF
          if (_isPrintablePdf && widget.hasExercisePdf) ...[
            Card(
              color: theme.colorScheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.picture_as_pdf,
                            color: theme.colorScheme.primary, size: 24),
                        const SizedBox(width: 8),
                        Text('Exercice à imprimer',
                            style: theme.textTheme.titleMedium
                                ?.copyWith(fontWeight: FontWeight.bold)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      '1. Téléchargez et imprimez le PDF\n'
                      '2. Résolvez l\'exercice sur papier\n'
                      '3. Prenez en photo votre solution',
                      style: TextStyle(fontSize: 13),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed:
                            _downloadingPdf ? null : _downloadExercisePdf,
                        icon: _downloadingPdf
                            ? const SizedBox(
                                height: 16,
                                width: 16,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.download),
                        label: Text(_downloadingPdf
                            ? 'Téléchargement...'
                            : 'Télécharger le PDF'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],

          // File picker buttons
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Ajouter des fichiers',
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(
                    'Max $_maxFiles fichiers, 50 MB max par fichier',
                    style: theme.textTheme.bodySmall
                        ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      _PickerButton(
                        icon: Icons.photo_library_outlined,
                        label: 'Galerie',
                        onTap: _uploading ? null : _pickFromGallery,
                      ),
                      const SizedBox(width: 12),
                      _PickerButton(
                        icon: Icons.camera_alt_outlined,
                        label: 'Caméra',
                        onTap: _uploading ? null : _pickFromCamera,
                      ),
                      const SizedBox(width: 12),
                      _PickerButton(
                        icon: Icons.description_outlined,
                        label: 'Documents',
                        onTap: _uploading ? null : _pickDocuments,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Selected files list
          if (_files.isNotEmpty) ...[
            Text('Fichiers sélectionnés (${_files.length}/$_maxFiles)',
                style: theme.textTheme.titleSmall
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            ..._files.asMap().entries.map((entry) {
              final index = entry.key;
              final file = entry.value;
              return Card(
                child: ListTile(
                  leading: file.isImage
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: Image.file(
                            File(file.path),
                            width: 48,
                            height: 48,
                            fit: BoxFit.cover,
                          ),
                        )
                      : Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: theme.colorScheme.primaryContainer,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Icon(
                            _iconForFile(file.name),
                            color: theme.colorScheme.primary,
                          ),
                        ),
                  title: Text(file.name,
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text(file.sizeLabel),
                  trailing: IconButton(
                    icon: Icon(Icons.close,
                        color: theme.colorScheme.error, size: 20),
                    onPressed: _uploading ? null : () => _removeFile(index),
                  ),
                ),
              );
            }),
            const SizedBox(height: 16),
          ],

          // Comment field
          TextFormField(
            controller: _commentController,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Commentaire (optionnel)',
              hintText: 'Ajoutez un commentaire à votre soumission...',
              border: OutlineInputBorder(),
              alignLabelWithHint: true,
            ),
            enabled: !_uploading,
          ),
          const SizedBox(height: 24),

          // Upload progress — determinate during PUT, indeterminate during scan
          if (_uploading) ...[
            Column(
              children: [
                _uploadProgress < 1.0
                    ? LinearProgressIndicator(value: _uploadProgress)
                    : const LinearProgressIndicator(),
                const SizedBox(height: 8),
                Text(
                  _uploadProgress < 1.0
                      ? 'Envoi... ${(_uploadProgress * 100).toStringAsFixed(0)}%'
                      : 'Analyse en cours…',
                  style: theme.textTheme.bodySmall,
                ),
              ],
            ),
            const SizedBox(height: 16),
          ],

          // Submit button
          FilledButton.icon(
            onPressed: _uploading || _files.isEmpty ? null : _upload,
            icon: _uploading
                ? SizedBox(
                    height: 16,
                    width: 16,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: theme.colorScheme.onPrimary))
                : const Icon(Icons.upload_file),
            label: Text(_uploading
                ? (_uploadProgress < 1.0 ? 'Envoi en cours...' : 'Analyse…')
                : 'Soumettre'),
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ],
      ),
    );
  }

  IconData _iconForFile(String name) {
    final ext = name.toLowerCase();
    if (ext.endsWith('.pdf')) return Icons.picture_as_pdf;
    if (ext.endsWith('.doc') || ext.endsWith('.docx')) return Icons.article;
    if (ext.endsWith('.xls') || ext.endsWith('.xlsx')) return Icons.table_chart;
    if (ext.endsWith('.txt')) return Icons.text_snippet;
    return Icons.insert_drive_file;
  }
}

class _PickerButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  const _PickerButton({
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
