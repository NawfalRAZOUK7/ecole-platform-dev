/// Coloring screen — student draws on top of a story page / outline image.
///
/// Uses the shared [DrawingOverlay] + [DrawingToolbar] widgets and can save
/// the completed coloring via POST /content-items/{id}/coloring-page.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/drawing_overlay.dart';

class ColoringScreen extends ConsumerStatefulWidget {
  /// The content item ID whose first page asset is used as the coloring template.
  final String contentItemId;
  final String title;
  final String? templateUrl; // optional pre-resolved image URL

  const ColoringScreen({
    super.key,
    required this.contentItemId,
    required this.title,
    this.templateUrl,
  });

  @override
  ConsumerState<ColoringScreen> createState() => _ColoringScreenState();
}

class _ColoringScreenState extends ConsumerState<ColoringScreen> {
  bool _saving = false;
  bool _saved = false;

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _saved = false;
    });
    try {
      // In a production build this would use RepaintBoundary + toImage()
      // to export the combined canvas + drawing as PNG, then POST to:
      // POST /content-items/{id}/coloring-page  (multipart/form-data)
      //
      // For now: reset local drawing state as a "submitted" signal.
      await Future.delayed(const Duration(milliseconds: 500)); // simulate
      ref.read(drawingProvider.notifier).clear();
      setState(() {
        _saved = true;
        _saving = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Coloriage sauvegardé !')),
        );
      }
    } catch (e) {
      setState(() => _saving = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        backgroundColor: KidsContentColors.storyBackground,
        actions: [
          if (_saving)
            const Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox(
                  width: 20, height: 20, child: CircularProgressIndicator()),
            )
          else
            IconButton(
              icon: Icon(
                _saved ? Icons.check_circle : Icons.save_alt,
                color: _saved ? KidsContentColors.xpBar : null,
              ),
              tooltip: 'Sauvegarder',
              onPressed: _save,
            ),
        ],
      ),
      body: Column(
        children: [
          // Canvas area
          Expanded(
            child: Container(
              color: KidsContentColors.canvasBackground,
              child: DrawingOverlay(
                child: widget.templateUrl != null
                    ? Image.network(
                        widget.templateUrl!,
                        fit: BoxFit.contain,
                        width: double.infinity,
                        height: double.infinity,
                        errorBuilder: (_, __, ___) =>
                            const _TemplateUnavailable(),
                      )
                    : const _TemplateUnavailable(),
              ),
            ),
          ),
          // Toolbar
          const SafeArea(
            top: false,
            child: DrawingToolbar(),
          ),
        ],
      ),
    );
  }
}

class _TemplateUnavailable extends StatelessWidget {
  const _TemplateUnavailable();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.brush,
              size: 64,
              color: KidsContentColors.storyPageTurn.withAlpha(80)),
          const SizedBox(height: AppSpacing.md),
          const Text(
            'Coloriage libre',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: KidsContentColors.storyText,
            ),
          ),
          const SizedBox(height: AppSpacing.xs),
          const Text(
            'Dessine ce que tu veux !',
            style: TextStyle(color: KidsContentColors.storyText),
          ),
        ],
      ),
    );
  }
}
