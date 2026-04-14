// ignore_for_file: library_private_types_in_public_api
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

// ---------------------------------------------------------------------------
// Data model
// ---------------------------------------------------------------------------

class _Stroke {
  final List<Offset> points;
  final Color color;
  final double width;
  final bool isEraser;

  const _Stroke({
    required this.points,
    required this.color,
    required this.width,
    this.isEraser = false,
  });
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

class DrawingState {
  final List<_Stroke> strokes;
  final Color selectedColor;
  final double strokeWidth;
  final bool isEraser;

  const DrawingState({
    this.strokes = const [],
    this.selectedColor = const Color(0xFF1565C0),
    this.strokeWidth = 4.0,
    this.isEraser = false,
  });

  DrawingState copyWith({
    List<_Stroke>? strokes,
    Color? selectedColor,
    double? strokeWidth,
    bool? isEraser,
  }) {
    return DrawingState(
      strokes: strokes ?? this.strokes,
      selectedColor: selectedColor ?? this.selectedColor,
      strokeWidth: strokeWidth ?? this.strokeWidth,
      isEraser: isEraser ?? this.isEraser,
    );
  }
}

// ---------------------------------------------------------------------------
// Notifier
// ---------------------------------------------------------------------------

class DrawingNotifier extends Notifier<DrawingState> {
  @override
  DrawingState build() => const DrawingState();

  void startStroke(Offset point) {
    final newStroke = _Stroke(
      points: [point],
      color: state.selectedColor,
      width: state.strokeWidth,
      isEraser: state.isEraser,
    );
    state = state.copyWith(strokes: [...state.strokes, newStroke]);
  }

  void addPoint(Offset point) {
    if (state.strokes.isEmpty) return;
    final last = state.strokes.last;
    final updated = _Stroke(
      points: [...last.points, point],
      color: last.color,
      width: last.width,
      isEraser: last.isEraser,
    );
    final strokes = [...state.strokes];
    strokes[strokes.length - 1] = updated;
    state = state.copyWith(strokes: strokes);
  }

  void endStroke() {
    // No-op — stroke is already committed; could trim empty strokes here.
  }

  void undo() {
    if (state.strokes.isEmpty) return;
    final strokes = [...state.strokes]..removeLast();
    state = state.copyWith(strokes: strokes);
  }

  void clear() => state = state.copyWith(strokes: []);

  void setColor(Color color) =>
      state = state.copyWith(selectedColor: color, isEraser: false);

  void setStrokeWidth(double width) =>
      state = state.copyWith(strokeWidth: width);

  void toggleEraser() =>
      state = state.copyWith(isEraser: !state.isEraser);
}

final drawingProvider = NotifierProvider<DrawingNotifier, DrawingState>(DrawingNotifier.new);

// ---------------------------------------------------------------------------
// CustomPainter
// ---------------------------------------------------------------------------

class _DrawingPainter extends CustomPainter {
  final List<_Stroke> strokes;

  const _DrawingPainter(this.strokes);

  @override
  void paint(Canvas canvas, Size size) {
    for (final stroke in strokes) {
      if (stroke.points.isEmpty) continue;
      final paint = Paint()
        ..color = stroke.isEraser ? Colors.white : stroke.color
        ..strokeWidth = stroke.isEraser ? stroke.width * 3 : stroke.width
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round
        ..style = PaintingStyle.stroke
        ..blendMode = stroke.isEraser ? ui.BlendMode.clear : ui.BlendMode.srcOver;

      final path = Path()..moveTo(stroke.points.first.dx, stroke.points.first.dy);
      for (int i = 1; i < stroke.points.length; i++) {
        final prev = stroke.points[i - 1];
        final curr = stroke.points[i];
        // Smooth with quadratic bezier
        path.quadraticBezierTo(
          prev.dx, prev.dy,
          (prev.dx + curr.dx) / 2,
          (prev.dy + curr.dy) / 2,
        );
      }
      canvas.drawPath(path, paint);
    }
  }

  @override
  bool shouldRepaint(_DrawingPainter oldDelegate) => oldDelegate.strokes != strokes;
}

// ---------------------------------------------------------------------------
// Drawing canvas widget
// ---------------------------------------------------------------------------

/// Transparent gesture-capture layer that renders user strokes on top of
/// any underlying widget (e.g., a story page image or coloring template).
///
/// Wrap any widget with [DrawingOverlay] to add draw-on-top capability.
class DrawingOverlay extends ConsumerWidget {
  final Widget child;

  const DrawingOverlay({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(drawingProvider);
    final notifier = ref.read(drawingProvider.notifier);

    return Stack(
      fit: StackFit.expand,
      children: [
        child,
        RepaintBoundary(
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onPanStart: (d) => notifier.startStroke(d.localPosition),
            onPanUpdate: (d) => notifier.addPoint(d.localPosition),
            onPanEnd: (_) => notifier.endStroke(),
            child: CustomPaint(
              painter: _DrawingPainter(state.strokes),
              size: Size.infinite,
            ),
          ),
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Color picker palette
// ---------------------------------------------------------------------------

const _kPalette = <Color>[
  Color(0xFF1565C0), // deep blue
  Color(0xFF2E7D32), // deep green
  Color(0xFFC62828), // deep red
  Color(0xFFFF6F00), // amber
  Color(0xFF6A1B9A), // purple
  Color(0xFF00838F), // teal
  Color(0xFF4E342E), // brown
  Color(0xFF000000), // black
  Color(0xFF757575), // grey
  Color(0xFFFFFFFF), // white
];

/// Horizontal color + tool palette bar for the drawing overlay.
///
/// Place below the canvas. Provides: color swatches, stroke width slider,
/// eraser toggle, undo, and clear.
class DrawingToolbar extends ConsumerWidget {
  const DrawingToolbar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(drawingProvider);
    final notifier = ref.read(drawingProvider.notifier);
    final theme = Theme.of(context);

    return Container(
      color: theme.colorScheme.surface,
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Color swatches row
          SizedBox(
            height: 36,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _kPalette.length,
              separatorBuilder: (_, __) => const SizedBox(width: AppSpacing.xs),
              itemBuilder: (context, i) {
                final color = _kPalette[i];
                final isSelected = !state.isEraser && state.selectedColor == color;
                return GestureDetector(
                  onTap: () => notifier.setColor(color),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 150),
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: color,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: isSelected
                            ? theme.colorScheme.primary
                            : KidsContentColors.colorPickerBorder,
                        width: isSelected ? 3 : 1,
                      ),
                      boxShadow: isSelected
                          ? [
                              BoxShadow(
                                color: theme.colorScheme.primary.withAlpha(80),
                                blurRadius: 4,
                              )
                            ]
                          : null,
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: AppSpacing.xs),
          // Tools row: stroke width + eraser + undo + clear
          Row(
            children: [
              const Icon(Icons.line_weight, size: 18),
              Expanded(
                child: Slider(
                  value: state.strokeWidth,
                  min: 2,
                  max: 20,
                  divisions: 9,
                  onChanged: notifier.setStrokeWidth,
                ),
              ),
              _ToolButton(
                icon: Icons.auto_fix_normal,
                label: 'Eraser',
                selected: state.isEraser,
                onTap: notifier.toggleEraser,
              ),
              _ToolButton(
                icon: Icons.undo,
                label: 'Undo',
                onTap: notifier.undo,
              ),
              _ToolButton(
                icon: Icons.delete_outline,
                label: 'Clear',
                onTap: notifier.clear,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ToolButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _ToolButton({
    required this.icon,
    required this.label,
    required this.onTap,
    this.selected = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: IconButton(
        icon: Icon(icon, size: 20),
        tooltip: label,
        style: IconButton.styleFrom(
          backgroundColor: selected
              ? theme.colorScheme.primaryContainer
              : Colors.transparent,
          foregroundColor: selected
              ? theme.colorScheme.onPrimaryContainer
              : theme.colorScheme.onSurface,
        ),
        onPressed: onTap,
      ),
    );
  }
}
