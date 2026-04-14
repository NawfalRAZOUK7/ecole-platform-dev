import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/ui/widgets/color_picker_palette.dart';

const double drawingStrokeThin = 2;
const double drawingStrokeMedium = 4;
const double drawingStrokeThick = 8;

@immutable
class DrawingPath {
  DrawingPath({
    required List<Offset> points,
    required this.color,
    required this.strokeWidth,
    this.isEraser = false,
  })  : points = List<Offset>.unmodifiable(points),
        path = _buildPath(points);

  final List<Offset> points;
  final Path path;
  final Color color;
  final double strokeWidth;
  final bool isEraser;

  DrawingPath copyWith({
    List<Offset>? points,
    Color? color,
    double? strokeWidth,
    bool? isEraser,
  }) {
    return DrawingPath(
      points: points ?? this.points,
      color: color ?? this.color,
      strokeWidth: strokeWidth ?? this.strokeWidth,
      isEraser: isEraser ?? this.isEraser,
    );
  }

  static Path _buildPath(List<Offset> points) {
    final path = Path();
    if (points.isEmpty) {
      return path;
    }

    path.moveTo(points.first.dx, points.first.dy);
    if (points.length == 1) {
      return path;
    }

    for (var index = 1; index < points.length; index++) {
      final previous = points[index - 1];
      final current = points[index];
      final midpoint = Offset(
        (previous.dx + current.dx) / 2,
        (previous.dy + current.dy) / 2,
      );
      path.quadraticBezierTo(
          previous.dx, previous.dy, midpoint.dx, midpoint.dy);
    }

    path.lineTo(points.last.dx, points.last.dy);
    return path;
  }
}

class DrawingOverlay extends StatefulWidget {
  const DrawingOverlay({
    super.key,
    required this.child,
    this.onDrawingChanged,
    this.backgroundColor = KidsContentColors.canvasBackground,
    this.showControls = true,
    this.initialPaths = const <DrawingPath>[],
  });

  final Widget child;
  final ValueChanged<List<DrawingPath>>? onDrawingChanged;
  final Color backgroundColor;
  final bool showControls;
  final List<DrawingPath> initialPaths;

  @override
  DrawingOverlayState createState() => DrawingOverlayState();
}

class DrawingOverlayState extends State<DrawingOverlay> {
  final GlobalKey _repaintBoundaryKey = GlobalKey();
  late List<DrawingPath> _paths;
  final List<DrawingPath> _redoStack = <DrawingPath>[];

  Color _selectedColor = kidFriendlyColorPalette.first;
  double _strokeWidth = drawingStrokeMedium;
  bool _isEraserMode = false;

  List<DrawingPath> get paths => List<DrawingPath>.unmodifiable(_paths);
  bool get canUndo => _paths.isNotEmpty;
  bool get canRedo => _redoStack.isNotEmpty;
  bool get isEraserMode => _isEraserMode;
  Color get selectedColor => _selectedColor;
  double get strokeWidth => _strokeWidth;

  @override
  void initState() {
    super.initState();
    _paths = List<DrawingPath>.of(widget.initialPaths);
  }

  @override
  void didUpdateWidget(covariant DrawingOverlay oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialPaths != widget.initialPaths && _paths.isEmpty) {
      _paths = List<DrawingPath>.of(widget.initialPaths);
    }
  }

  void setSelectedColor(Color color) {
    setState(() {
      _selectedColor = color;
      _isEraserMode = false;
    });
  }

  void setStrokeWidth(double width) {
    setState(() {
      _strokeWidth = width;
    });
  }

  void toggleEraser() {
    setState(() {
      _isEraserMode = !_isEraserMode;
    });
  }

  void undo() {
    if (_paths.isEmpty) {
      return;
    }

    setState(() {
      _redoStack.add(_paths.removeLast());
    });
    _notifyDrawingChanged();
  }

  void redo() {
    if (_redoStack.isEmpty) {
      return;
    }

    setState(() {
      _paths.add(_redoStack.removeLast());
    });
    _notifyDrawingChanged();
  }

  void clearAll() {
    if (_paths.isEmpty && _redoStack.isEmpty) {
      return;
    }

    setState(() {
      _paths = <DrawingPath>[];
      _redoStack.clear();
    });
    _notifyDrawingChanged();
  }

  Future<Uint8List?> exportAsImage({double pixelRatio = 3}) async {
    final boundaryContext = _repaintBoundaryKey.currentContext;
    if (boundaryContext == null) {
      return null;
    }

    final boundary =
        boundaryContext.findRenderObject() as RenderRepaintBoundary?;
    if (boundary == null) {
      return null;
    }

    final image = await boundary.toImage(pixelRatio: pixelRatio);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    return bytes?.buffer.asUint8List();
  }

  void _startStroke(Offset position) {
    final stroke = DrawingPath(
      points: <Offset>[position],
      color: _isEraserMode ? widget.backgroundColor : _selectedColor,
      strokeWidth: _strokeWidth,
      isEraser: _isEraserMode,
    );

    setState(() {
      _paths = <DrawingPath>[..._paths, stroke];
      _redoStack.clear();
    });
    _notifyDrawingChanged();
  }

  void _appendPoint(Offset position) {
    if (_paths.isEmpty) {
      return;
    }

    final current = _paths.last;
    final updated =
        current.copyWith(points: <Offset>[...current.points, position]);
    setState(() {
      _paths = <DrawingPath>[
        ..._paths.take(_paths.length - 1),
        updated,
      ];
    });
    _notifyDrawingChanged();
  }

  void _notifyDrawingChanged() {
    widget.onDrawingChanged?.call(List<DrawingPath>.unmodifiable(_paths));
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: <Widget>[
        RepaintBoundary(
          key: _repaintBoundaryKey,
          child: Stack(
            fit: StackFit.expand,
            children: <Widget>[
              widget.child,
              Positioned.fill(
                child: GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onPanStart: (details) => _startStroke(details.localPosition),
                  onPanUpdate: (details) => _appendPoint(details.localPosition),
                  child: CustomPaint(
                    painter: _DrawingPainter(paths: _paths),
                    size: Size.infinite,
                  ),
                ),
              ),
            ],
          ),
        ),
        if (widget.showControls)
          Positioned(
            left: AppSpacing.base,
            right: AppSpacing.base,
            bottom: AppSpacing.base,
            child: SafeArea(
              top: false,
              child: _DrawingControls(
                selectedColor: _selectedColor,
                strokeWidth: _strokeWidth,
                isEraserMode: _isEraserMode,
                canUndo: canUndo,
                canRedo: canRedo,
                onColorSelected: setSelectedColor,
                onStrokeWidthSelected: setStrokeWidth,
                onEraserToggled: toggleEraser,
                onUndo: undo,
                onRedo: redo,
                onClearAll: clearAll,
              ),
            ),
          ),
      ],
    );
  }
}

class _DrawingPainter extends CustomPainter {
  const _DrawingPainter({required this.paths});

  final List<DrawingPath> paths;

  @override
  void paint(Canvas canvas, Size size) {
    for (final drawingPath in paths) {
      if (drawingPath.points.isEmpty) {
        continue;
      }

      final paint = Paint()
        ..color = drawingPath.color
        ..strokeWidth = drawingPath.strokeWidth
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round
        ..style = PaintingStyle.stroke;

      if (drawingPath.points.length == 1) {
        canvas.drawCircle(
          drawingPath.points.first,
          drawingPath.strokeWidth / 2,
          paint..style = PaintingStyle.fill,
        );
        continue;
      }

      canvas.drawPath(drawingPath.path, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _DrawingPainter oldDelegate) {
    return oldDelegate.paths != paths;
  }
}

class _DrawingControls extends StatelessWidget {
  const _DrawingControls({
    required this.selectedColor,
    required this.strokeWidth,
    required this.isEraserMode,
    required this.canUndo,
    required this.canRedo,
    required this.onColorSelected,
    required this.onStrokeWidthSelected,
    required this.onEraserToggled,
    required this.onUndo,
    required this.onRedo,
    required this.onClearAll,
  });

  final Color selectedColor;
  final double strokeWidth;
  final bool isEraserMode;
  final bool canUndo;
  final bool canRedo;
  final ValueChanged<Color> onColorSelected;
  final ValueChanged<double> onStrokeWidthSelected;
  final VoidCallback onEraserToggled;
  final VoidCallback onUndo;
  final VoidCallback onRedo;
  final VoidCallback onClearAll;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withAlpha(235),
        borderRadius: BorderRadius.circular(20),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withAlpha(24),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Palette de dessin',
              style: theme.textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            ColorPickerPalette(
              selectedColor: selectedColor,
              onColorSelected: onColorSelected,
            ),
            const SizedBox(height: AppSpacing.md),
            Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: <Widget>[
                _StrokeWidthChip(
                  label: 'Fin',
                  width: drawingStrokeThin,
                  selected: strokeWidth == drawingStrokeThin,
                  onSelected: onStrokeWidthSelected,
                ),
                _StrokeWidthChip(
                  label: 'Moyen',
                  width: drawingStrokeMedium,
                  selected: strokeWidth == drawingStrokeMedium,
                  onSelected: onStrokeWidthSelected,
                ),
                _StrokeWidthChip(
                  label: 'Épais',
                  width: drawingStrokeThick,
                  selected: strokeWidth == drawingStrokeThick,
                  onSelected: onStrokeWidthSelected,
                ),
                _ControlButton(
                  icon: Icons.auto_fix_normal_outlined,
                  label: 'Gomme',
                  selected: isEraserMode,
                  onPressed: onEraserToggled,
                ),
                _ControlButton(
                  icon: Icons.undo_rounded,
                  label: 'Annuler',
                  enabled: canUndo,
                  onPressed: onUndo,
                ),
                _ControlButton(
                  icon: Icons.redo_rounded,
                  label: 'Rétablir',
                  enabled: canRedo,
                  onPressed: onRedo,
                ),
                _ControlButton(
                  icon: Icons.delete_sweep_rounded,
                  label: 'Effacer',
                  onPressed: onClearAll,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StrokeWidthChip extends StatelessWidget {
  const _StrokeWidthChip({
    required this.label,
    required this.width,
    required this.selected,
    required this.onSelected,
  });

  final String label;
  final double width;
  final bool selected;
  final ValueChanged<double> onSelected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ChoiceChip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text(label),
          const SizedBox(width: AppSpacing.xs),
          Container(
            width: 18,
            height: width,
            decoration: BoxDecoration(
              color: theme.colorScheme.onSurface,
              borderRadius: BorderRadius.circular(width),
            ),
          ),
        ],
      ),
      selected: selected,
      onSelected: (_) => onSelected(width),
    );
  }
}

class _ControlButton extends StatelessWidget {
  const _ControlButton({
    required this.icon,
    required this.label,
    required this.onPressed,
    this.selected = false,
    this.enabled = true,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;
  final bool selected;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final foregroundColor = selected
        ? theme.colorScheme.onPrimaryContainer
        : theme.colorScheme.onSurface;

    return FilledButton.tonalIcon(
      onPressed: enabled ? onPressed : null,
      style: FilledButton.styleFrom(
        backgroundColor: selected ? theme.colorScheme.primaryContainer : null,
        foregroundColor: foregroundColor,
        disabledForegroundColor: theme.colorScheme.onSurface.withAlpha(120),
      ),
      icon: Icon(icon, size: 18),
      label: Text(label),
    );
  }
}
