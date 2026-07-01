/**
 * useSpeech — small wrapper over the browser-native Web Speech API
 * (`window.speechSynthesis`) with a hybrid rule: play an existing audio file
 * when one is provided, otherwise speak the text via TTS.
 *
 * This is the web counterpart of the mobile `TtsService` (flutter_tts).
 * No external dependency — speechSynthesis is built into modern browsers.
 */

import { useCallback, useEffect, useRef } from 'react';

export type SpeechLang = 'ar' | 'fr' | 'en';

const LOCALE: Record<SpeechLang, string> = {
  ar: 'ar-SA',
  fr: 'fr-FR',
  en: 'en-US',
};

function ttsSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

/** Pick the best available voice for a language, falling back gracefully. */
function pickVoice(lang: SpeechLang): SpeechSynthesisVoice | undefined {
  if (!ttsSupported()) return undefined;
  const voices = window.speechSynthesis.getVoices();
  const locale = LOCALE[lang];
  return (
    voices.find((v) => v.lang === locale) ??
    voices.find((v) => v.lang.startsWith(lang)) ??
    undefined
  );
}

export interface SpeakOptions {
  /** If provided, play this audio file instead of synthesizing speech. */
  audioUrl?: string | null;
  lang?: SpeechLang;
  rate?: number;
  pitch?: number;
}

export function useSpeech() {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Warm up the voice list (some browsers populate it asynchronously).
  useEffect(() => {
    if (!ttsSupported()) return;
    const handler = () => window.speechSynthesis.getVoices();
    handler();
    window.speechSynthesis.addEventListener?.('voiceschanged', handler);
    return () => {
      window.speechSynthesis.removeEventListener?.('voiceschanged', handler);
    };
  }, []);

  const stop = useCallback(() => {
    if (ttsSupported()) window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  }, []);

  const speak = useCallback(
    (text: string, options: SpeakOptions = {}) => {
      const { audioUrl, lang = 'ar', rate = 0.9, pitch = 1.05 } = options;
      stop();

      // Hybrid rule: prefer an existing audio file.
      if (audioUrl) {
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        void audio.play().catch(() => {
          // Autoplay blocked or file missing — fall back to TTS.
          audioRef.current = null;
          ttsSpeak(text, lang, rate, pitch);
        });
        return;
      }
      ttsSpeak(text, lang, rate, pitch);
    },
    [stop],
  );

  function ttsSpeak(text: string, lang: SpeechLang, rate: number, pitch: number) {
    if (!ttsSupported() || !text) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = LOCALE[lang];
    utter.rate = rate;
    utter.pitch = pitch;
    const voice = pickVoice(lang);
    if (voice) utter.voice = voice;
    window.speechSynthesis.speak(utter);
  }

  // Stop any speech/audio when the component using the hook unmounts.
  useEffect(() => stop, [stop]);

  return { speak, stop, supported: ttsSupported() };
}
