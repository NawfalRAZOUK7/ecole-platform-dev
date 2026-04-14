import 'dart:async';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// App-wide Arabic text-to-speech service backed by [FlutterTts].
class TtsService {
  TtsService({FlutterTts? flutterTts}) : _tts = flutterTts ?? FlutterTts();

  static const String _defaultLocale = 'ar-SA';
  static const Duration _instructionDelay = Duration(milliseconds: 250);
  static const List<String> _praisePhrases = <String>[
    'أحسنت!',
    'ممتاز!',
    'رائع!',
    'بطل!',
    'عمل جميل!',
  ];
  static const Map<String, String> _letterExamples = <String, String>{
    'أ': 'أرنب',
    'ب': 'بطة',
    'ت': 'تفاحة',
    'ث': 'ثعلب',
    'ج': 'جمل',
    'ح': 'حصان',
    'خ': 'خروف',
    'د': 'ديك',
    'ذ': 'ذرة',
    'ر': 'رمان',
    'ز': 'زهرة',
    'س': 'سمكة',
    'ش': 'شمس',
    'ص': 'صقر',
    'ض': 'ضفدع',
    'ط': 'طائر',
    'ظ': 'ظبي',
    'ع': 'عصفور',
    'غ': 'غزال',
    'ف': 'فراشة',
    'ق': 'قمر',
    'ك': 'كتاب',
    'ل': 'ليمون',
    'م': 'موز',
    'ن': 'نحلة',
    'ه': 'هلال',
    'و': 'وردة',
    'ي': 'يد',
  };

  final FlutterTts _tts;
  final Random _random = Random();

  Future<void>? _initFuture;
  bool _disposed = false;
  bool _isSpeaking = false;
  double _speed = 0.45;
  final double _pitch = 1.05;
  double _volume = 1.0;

  bool get isSpeaking => _isSpeaking;

  /// Configure the engine for Arabic speech with kid-friendly defaults.
  Future<void> init() {
    if (_disposed) {
      return Future.value();
    }
    return _initFuture ??= _configure();
  }

  Future<void> _configure() async {
    _tts.setStartHandler(() => _isSpeaking = true);
    _tts.setCompletionHandler(() => _isSpeaking = false);
    _tts.setCancelHandler(() => _isSpeaking = false);
    _tts.setPauseHandler(() => _isSpeaking = false);
    _tts.setErrorHandler((message) {
      _isSpeaking = false;
      debugPrint('[TTS] $message');
    });

    await _tts.awaitSpeakCompletion(true);
    await _tts.setLanguage(_defaultLocale);
    await _tts.setSpeechRate(_speed);
    await _tts.setPitch(_pitch);
    await _tts.setVolume(_volume);
  }

  Future<void> _ensureInitialized() async {
    await init();
  }

  Future<void> _speak(String text) async {
    if (_disposed) return;
    final normalized = text.trim();
    if (normalized.isEmpty) return;

    await _ensureInitialized();
    await _tts.stop();
    await _tts.speak(normalized);
  }

  /// Speak general-purpose Arabic text.
  Future<void> speakText(String text) async {
    await _speak(text);
  }

  /// Speak a letter with a simple example word.
  Future<void> speakLetter(String letter) async {
    final normalized = letter.trim();
    if (normalized.isEmpty) return;

    final example = _letterExamples[normalized];
    final phrase = example == null
        ? 'حرف $normalized'
        : 'حرف $normalized. $normalized مثل $example';
    await _speak(phrase);
  }

  /// Speak a random praise phrase.
  Future<void> speakPraise() async {
    final phrase = _praisePhrases[_random.nextInt(_praisePhrases.length)];
    await _speak(phrase);
  }

  /// Speak an instruction after a small delay.
  Future<void> speakInstruction(String text) async {
    if (_disposed) return;
    final normalized = text.trim();
    if (normalized.isEmpty) return;

    await stop();
    await Future.delayed(_instructionDelay);
    await _speak(normalized);
  }

  Future<void> setSpeed(double value) async {
    _speed = value.clamp(0.1, 1.0).toDouble();
    await _ensureInitialized();
    await _tts.setSpeechRate(_speed);
  }

  Future<void> setVolume(double value) async {
    _volume = value.clamp(0.0, 1.0).toDouble();
    await _ensureInitialized();
    await _tts.setVolume(_volume);
  }

  Future<void> stop() async {
    if (_disposed) return;
    if (_initFuture == null) {
      _isSpeaking = false;
      return;
    }
    await _ensureInitialized();
    await _tts.stop();
    _isSpeaking = false;
  }

  Future<void> dispose() async {
    if (_disposed) return;
    await stop();
    _disposed = true;
  }
}
