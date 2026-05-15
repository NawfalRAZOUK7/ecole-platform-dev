import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';
import 'package:pdf_render/pdf_render_widgets.dart';
import 'package:share_plus/share_plus.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/content/document_management.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/signed_network_image.dart';

class DocumentPreviewScreen extends ConsumerStatefulWidget {
  final ManagedDocument? document;
  final ResourceLibraryItem? resource;

  const DocumentPreviewScreen({
    super.key,
    this.document,
    this.resource,
  });

  @override
  ConsumerState<DocumentPreviewScreen> createState() =>
      _DocumentPreviewScreenState();
}

class _DocumentPreviewScreenState extends ConsumerState<DocumentPreviewScreen> {
  File? _localFile;
  bool _loading = false;
  String? _error;

  ManagedDocument? get _document =>
      widget.document ?? widget.resource?.document;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _prepare();
    });
  }

  Future<void> _prepare() async {
    final document = _document;
    if (document == null) {
      setState(() => _error = 'Missing document payload');
      return;
    }

    if (document.availableOffline) {
      final file = File(document.localFilePath!);
      if (await file.exists()) {
        if (!mounted) return;
        setState(() => _localFile = file);
        return;
      }
    }

    if (document.isPdf ||
        document.previewUrl == null ||
        document.previewUrl!.isEmpty) {
      await _downloadForOffline(showSuccessMessage: false);
    }
  }

  Future<File> _downloadForOffline({bool showSuccessMessage = true}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final file = widget.resource != null
          ? await ref
              .read(documentRepositoryProvider)
              .downloadResourceFile(widget.resource!)
          : await ref
              .read(documentRepositoryProvider)
              .downloadDocumentFile(widget.document!);
      if (!mounted) return file;
      setState(() {
        _localFile = file;
        _loading = false;
      });
      if (showSuccessMessage) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(ref).t('documents.savedOffline')),
          ),
        );
      }
      return file;
    } catch (e) {
      if (!mounted) rethrow;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
      rethrow;
    }
  }

  Future<void> _share() async {
    try {
      final file =
          _localFile ?? await _downloadForOffline(showSuccessMessage: false);
      await Share.shareXFiles(
        [XFile(file.path)],
        text: _document?.originalFilename ?? widget.resource?.title ?? '',
      );
    } catch (_) {
      // Handled in download.
    }
  }

  Future<void> _openExternally() async {
    try {
      final file =
          _localFile ?? await _downloadForOffline(showSuccessMessage: false);
      final result = await OpenFilex.open(file.path);
      if (!mounted) return;
      if (result.type != ResultType.done) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result.message)),
        );
      }
    } catch (_) {
      // Handled in download.
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final document = _document;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.resource?.title ??
              document?.originalFilename ??
              t.t('documents.preview'),
        ),
        actions: [
          IconButton(
            onPressed: _loading ? null : _share,
            icon: const Icon(Icons.share_outlined),
          ),
          IconButton(
            onPressed: _loading ? null : _openExternally,
            icon: const Icon(Icons.open_in_new_outlined),
          ),
          IconButton(
            onPressed: _loading ? null : _downloadForOffline,
            icon: const Icon(Icons.download_outlined),
          ),
        ],
      ),
      body: _buildBody(document, t),
    );
  }

  Widget _buildBody(ManagedDocument? document, AppLocalizations t) {
    if (document == null) {
      return Center(child: Text(t.t('documents.empty')));
    }

    if (_loading && document.isPdf && _localFile == null) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null && _localFile == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            _error!,
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    if (document.isPdf) {
      if (_localFile == null) {
        return const Center(child: CircularProgressIndicator());
      }
      return PdfViewer.openFile(_localFile!.path);
    }

    if (document.isImage) {
      if (_localFile != null) {
        return InteractiveViewer(
          minScale: 1,
          maxScale: 5,
          child: Center(child: Image.file(_localFile!)),
        );
      }
      final previewUrl = document.previewUrl ?? document.thumbnailUrl;
      if (previewUrl == null || previewUrl.isEmpty) {
        return Center(child: Text(t.t('documents.previewUnavailable')));
      }
      return InteractiveViewer(
        minScale: 1,
        maxScale: 5,
        child: Center(
          child: SignedNetworkImage(
            path: previewUrl,
            fit: BoxFit.contain,
          ),
        ),
      );
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.insert_drive_file_outlined, size: 72),
            const SizedBox(height: 16),
            Text(document.originalFilename, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            Text(t.t('documents.previewUnavailable')),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _share,
              icon: const Icon(Icons.share_outlined),
              label: Text(t.t('documents.share')),
            ),
          ],
        ),
      ),
    );
  }
}
