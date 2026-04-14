import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTypography {
  const AppTypography._();

  static TextStyle get heading1 => GoogleFonts.cairo(
        fontSize: 28,
        fontWeight: FontWeight.bold,
      );
  static TextStyle get heading2 => GoogleFonts.cairo(
        fontSize: 24,
        fontWeight: FontWeight.bold,
      );
  static TextStyle get heading3 => GoogleFonts.cairo(
        fontSize: 20,
        fontWeight: FontWeight.w600,
      );
  static TextStyle get heading4 => GoogleFonts.cairo(
        fontSize: 18,
        fontWeight: FontWeight.w600,
      );
  static TextStyle get body => GoogleFonts.cairo(
        fontSize: 16,
        fontWeight: FontWeight.normal,
      );
  static TextStyle get bodySmall => GoogleFonts.cairo(
        fontSize: 14,
        fontWeight: FontWeight.normal,
      );
  static TextStyle get caption => GoogleFonts.cairo(
        fontSize: 12,
        fontWeight: FontWeight.normal,
      );
  static TextStyle get label => GoogleFonts.cairo(
        fontSize: 14,
        fontWeight: FontWeight.w500,
      );
}
