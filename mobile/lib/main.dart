/// École Platform — Mobile App Entry Point
///
/// 3-layer architecture per Pack E2:
/// - presentation/ — Screens, widgets, navigation, view-models
/// - domain/ — Use-cases, business rules, repository interfaces
/// - data/ — API client, DTOs, persistence, cache
///
/// State management: Riverpod (DEC-E2-002)
/// Offline: SQLite with TTL policies (DEC-E2-020)

import 'package:flutter/material.dart';

void main() {
  runApp(const EcolePlatformApp());
}

class EcolePlatformApp extends StatelessWidget {
  const EcolePlatformApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'École Platform',
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF0B5FFF), // color.primary.500
        useMaterial3: true,
        fontFamily: 'Inter', // font.body.family per E5
      ),
      home: const Scaffold(
        body: Center(
          child: Text('École Platform — Mobile app skeleton.\nSprint 6 will add auth, navigation, and features.'),
        ),
      ),
    );
  }
}
