/// Static École Platform logo mark, painted (no asset dependency).
///
/// Draws the rounded gradient tile + ring + graduation cap + amber tassel bead,
/// matching the web `ecole-icon.svg`. Use anywhere a branded logo is needed
/// (login, empty states, headers). Set [tile] to false to paint the white mark
/// only (e.g. on an existing coloured surface).

import 'package:flutter/material.dart';

class EcoleLogoMark extends StatelessWidget {
  final double size;
  final bool tile;

  const EcoleLogoMark({super.key, this.size = 96, this.tile = true});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _EcoleLogoPainter(tile: tile)),
    );
  }
}

class _EcoleLogoPainter extends CustomPainter {
  final bool tile;

  _EcoleLogoPainter({required this.tile});

  @override
  void paint(Canvas canvas, Size size) {
    final f = size.width / 100.0;
    Offset p(double x, double y) => Offset(x * f, y * f);

    if (tile) {
      final tileRect = RRect.fromRectAndRadius(
        Rect.fromLTWH(3 * f, 3 * f, 94 * f, 94 * f),
        Radius.circular(22 * f),
      );
      final tilePaint = Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF2563EB), Color(0xFF5B5BEF), Color(0xFF8B5CF6)],
          stops: [0.0, 0.55, 1.0],
        ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
      canvas.drawRRect(tileRect, tilePaint);
    }

    // Ring.
    canvas.drawCircle(
      p(50, 48.4),
      33.2 * f,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.2 * f
        ..color = Colors.white.withAlpha(tile ? 70 : 110),
    );

    // Graduation cap.
    final white = Paint()..color = Colors.white;
    final board = Path()
      ..moveTo(p(50, 29.3).dx, p(50, 29.3).dy)
      ..lineTo(p(78.5, 41.8).dx, p(78.5, 41.8).dy)
      ..lineTo(p(50, 54.3).dx, p(50, 54.3).dy)
      ..lineTo(p(21.5, 41.8).dx, p(21.5, 41.8).dy)
      ..close();
    canvas.drawPath(board, white);
    final cup = Path()
      ..moveTo(p(43.4, 52).dx, p(43.4, 52).dy)
      ..lineTo(p(56.6, 52).dx, p(56.6, 52).dy)
      ..lineTo(p(55.5, 58.6).dx, p(55.5, 58.6).dy)
      ..lineTo(p(50, 61.7).dx, p(50, 61.7).dy)
      ..lineTo(p(44.5, 58.6).dx, p(44.5, 58.6).dy)
      ..close();
    canvas.drawPath(cup, white);
    canvas.drawCircle(p(50, 41.8), 2.3 * f, white);

    // Tassel + amber bead.
    canvas.drawLine(
      p(78.5, 41.8),
      p(78.5, 58.6),
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.4 * f
        ..strokeCap = StrokeCap.round
        ..color = Colors.white,
    );
    canvas.drawCircle(p(78.5, 61.7), 2.7 * f, Paint()..color = const Color(0xFFF59E0B));
  }

  @override
  bool shouldRepaint(_EcoleLogoPainter old) => old.tile != tile;
}
