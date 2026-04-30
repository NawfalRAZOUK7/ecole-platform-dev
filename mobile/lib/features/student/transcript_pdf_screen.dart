import 'dart:io';

import 'package:flutter/material.dart';
import 'package:open_filex/open_filex.dart';
import 'package:pdf_render/pdf_render_widgets.dart';
import 'package:share_plus/share_plus.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

class TranscriptPdfScreen extends StatelessWidget {
  final String title;
  final String filePath;

  const TranscriptPdfScreen({
    super.key,
    required this.title,
    required this.filePath,
  });

  Future<void> _share(BuildContext context) async {
    await Share.shareXFiles([XFile(filePath)], text: title);
  }

  Future<void> _openExternally(BuildContext context) async {
    final result = await OpenFilex.open(filePath);
    if (!context.mounted || result.type == ResultType.done) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(result.message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final file = File(filePath);
    final locale = Localizations.localeOf(context).languageCode;
    final t = AppLocalizations(locale);

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            onPressed: () => _share(context),
            icon: const Icon(Icons.share_outlined),
            tooltip: t.t('documents.share'),
          ),
          IconButton(
            onPressed: () => _openExternally(context),
            icon: const Icon(Icons.open_in_new_outlined),
            tooltip: t.t('academicHistory.openExternal'),
          ),
        ],
      ),
      body: file.existsSync()
          ? PdfViewer.openFile(filePath)
          : AppErrorWidget(message: t.t('academicHistory.viewerMissing')),
    );
  }
}
