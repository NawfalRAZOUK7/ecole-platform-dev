import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/shared/services/tts_service.dart';

class MockFlutterTts extends Mock implements FlutterTts {}

void main() {
  late MockFlutterTts mockTts;
  late TtsService service;

  setUp(() {
    mockTts = MockFlutterTts();

    // Default stubs — all async ops succeed
    when(() => mockTts.awaitSpeakCompletion(any())).thenAnswer((_) async => 1);
    when(() => mockTts.setLanguage(any())).thenAnswer((_) async => 1);
    when(() => mockTts.setSpeechRate(any())).thenAnswer((_) async => 1);
    when(() => mockTts.setPitch(any())).thenAnswer((_) async => 1);
    when(() => mockTts.setVolume(any())).thenAnswer((_) async => 1);
    when(() => mockTts.speak(any())).thenAnswer((_) async => 1);
    when(() => mockTts.stop()).thenAnswer((_) async => 1);

    // Handler setters — capture but do nothing
    when(() => mockTts.setStartHandler(any())).thenReturn(null);
    when(() => mockTts.setCompletionHandler(any())).thenReturn(null);
    when(() => mockTts.setCancelHandler(any())).thenReturn(null);
    when(() => mockTts.setPauseHandler(any())).thenReturn(null);
    when(() => mockTts.setErrorHandler(any())).thenReturn(null);

    service = TtsService(flutterTts: mockTts);
  });

  group('TtsService', () {
    group('init / configure', () {
      test('init configures TTS engine with default settings', () async {
        await service.init();

        verify(() => mockTts.setLanguage('ar-SA')).called(1);
        verify(() => mockTts.setSpeechRate(any())).called(1);
        verify(() => mockTts.setPitch(any())).called(1);
        verify(() => mockTts.setVolume(any())).called(1);
      });

      test('second init() call is a no-op (cached future)', () async {
        await service.init();
        await service.init();

        // setLanguage is only called once
        verify(() => mockTts.setLanguage(any())).called(1);
      });
    });

    group('speakText', () {
      test('speaks the provided text', () async {
        await service.speakText('مرحبا');

        verify(() => mockTts.speak('مرحبا')).called(1);
      });

      test('trims whitespace before speaking', () async {
        await service.speakText('  أهلا  ');

        verify(() => mockTts.speak('أهلا')).called(1);
      });

      test('does nothing for empty string', () async {
        await service.speakText('   ');

        verifyNever(() => mockTts.speak(any()));
      });
    });

    group('speakLetter', () {
      test('speaks letter with known example word', () async {
        await service.speakLetter('أ');

        final captured = verify(() => mockTts.speak(captureAny())).captured;
        expect(captured.first as String, contains('أ'));
        expect(captured.first as String, contains('أرنب'));
      });

      test('speaks fallback phrase for unknown letter', () async {
        await service.speakLetter('X');

        final captured = verify(() => mockTts.speak(captureAny())).captured;
        expect(captured.first as String, contains('حرف X'));
      });

      test('does nothing for empty string', () async {
        await service.speakLetter('');

        verifyNever(() => mockTts.speak(any()));
      });

      test('trims whitespace from letter', () async {
        await service.speakLetter('  ب  ');

        final captured = verify(() => mockTts.speak(captureAny())).captured;
        expect(captured.first as String, contains('ب'));
      });
    });

    group('speakPraise', () {
      test('speaks a non-empty praise phrase', () async {
        await service.speakPraise();

        final captured = verify(() => mockTts.speak(captureAny())).captured;
        expect((captured.first as String).isNotEmpty, isTrue);
      });

      test('always calls speak once', () async {
        await service.speakPraise();
        verify(() => mockTts.speak(any())).called(1);
      });
    });

    group('speakInstruction', () {
      test('stops then speaks the instruction text', () async {
        await service.speakInstruction('استمع جيداً');

        verify(() => mockTts.stop()).called(greaterThan(0));
        verify(() => mockTts.speak('استمع جيداً')).called(1);
      });

      test('does nothing for empty instruction', () async {
        await service.speakInstruction('');

        verifyNever(() => mockTts.speak(any()));
      });
    });

    group('setSpeed', () {
      test('updates speech rate within valid range', () async {
        await service.init(); // prime the init
        await service.setSpeed(0.6);

        // setSpeechRate is called during init (0.45) and again for the update
        verify(() => mockTts.setSpeechRate(any())).called(greaterThan(1));
      });

      test('clamps speed to [0.1, 1.0]', () async {
        await service.init();
        await service.setSpeed(5.0); // above max

        final calls = verify(() => mockTts.setSpeechRate(captureAny())).captured;
        final last = calls.last as double;
        expect(last, lessThanOrEqualTo(1.0));
      });
    });

    group('setVolume', () {
      test('updates volume within valid range', () async {
        await service.init();
        await service.setVolume(0.8);

        verify(() => mockTts.setVolume(any())).called(greaterThan(1));
      });

      test('clamps volume to [0.0, 1.0]', () async {
        await service.init();
        await service.setVolume(-1.0); // below min

        final calls = verify(() => mockTts.setVolume(captureAny())).captured;
        final last = calls.last as double;
        expect(last, greaterThanOrEqualTo(0.0));
      });
    });

    group('stop', () {
      test('calls tts.stop when initialized', () async {
        await service.speakText('test'); // initializes
        await service.stop();

        verify(() => mockTts.stop()).called(greaterThan(0));
      });

      test('no-ops without initialization', () async {
        await service.stop();

        verifyNever(() => mockTts.stop());
      });
    });

    group('isSpeaking', () {
      test('starts as false', () {
        expect(service.isSpeaking, isFalse);
      });
    });

    group('dispose', () {
      test('stops tts and marks as disposed', () async {
        await service.init();
        await service.dispose();

        // After dispose, speakText should not call speak
        await service.speakText('après dispose');
        verifyNever(() => mockTts.speak(any()));
      });

      test('second dispose is a no-op', () async {
        await service.dispose();
        await service.dispose(); // should not throw
      });
    });
  });
}
