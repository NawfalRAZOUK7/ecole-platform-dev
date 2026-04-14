import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// TTS playback state
enum TtsState { stopped, playing, paused }

/// Riverpod notifier that wraps [FlutterTts] for app-wide text-to-speech.
///
/// Usage:
/// ```dart
/// final tts = ref.read(ttsServiceProvider.notifier);
/// await tts.speak("مرحباً بكم في قصة اليوم");
/// ```
class TtsService extends Notifier<TtsState> {
  late final FlutterTts _tts;

  @override
  TtsState build() {
    _tts = FlutterTts();
    _init();
    ref.onDispose(_tts.stop);
    return TtsState.stopped;
  }

  void _init() {
    _tts.setStartHandler(() => state = TtsState.playing);
    _tts.setCompletionHandler(() => state = TtsState.stopped);
    _tts.setCancelHandler(() => state = TtsState.stopped);
    _tts.setPauseHandler(() => state = TtsState.paused);
    _tts.setContinueHandler(() => state = TtsState.playing);
    _tts.setErrorHandler((msg) {
      state = TtsState.stopped;
      debugPrint('[TTS] error: $msg');
    });
  }

  /// Configure language and speech rate for kids content.
  /// Call once per session (or when language changes).
  Future<void> configure({
    String language = 'ar-DZ',
    double speechRate = 0.45,
    double pitch = 1.1,
    double volume = 1.0,
  }) async {
    await _tts.setLanguage(language);
    await _tts.setSpeechRate(speechRate);
    await _tts.setPitch(pitch);
    await _tts.setVolume(volume);
  }

  /// Speak [text]. Stops any ongoing speech first.
  Future<void> speak(String text) async {
    if (text.trim().isEmpty) return;
    if (state == TtsState.playing) await _tts.stop();
    await configure();
    await _tts.speak(text);
  }

  /// Pause ongoing speech (Android / iOS 7+).
  Future<void> pause() async {
    if (state == TtsState.playing) await _tts.pause();
  }

  /// Stop speech immediately.
  Future<void> stop() async {
    await _tts.stop();
    state = TtsState.stopped;
  }

  /// Toggle play/pause for the given [text].
  Future<void> toggle(String text) async {
    switch (state) {
      case TtsState.stopped:
        await speak(text);
      case TtsState.playing:
        await pause();
      case TtsState.paused:
        // flutter_tts does not support true resume — re-speak from start
        await speak(text);
    }
  }

  bool get isPlaying => state == TtsState.playing;
  bool get isStopped => state == TtsState.stopped;
}

final ttsServiceProvider = NotifierProvider<TtsService, TtsState>(TtsService.new);
