import os
import re
import time
import uuid

import keyboard
import numpy as np
import sounddevice as sd
import threading

from modules.local_speech import LocalSpeechRecognizer, LocalTTS, pcm_to_wav_bytes


class VoiceManager:
    """Entrada e saída local: faster-whisper + Piper/Kokoro, com SAPI de reserva."""

    LANGUAGE_CODES = {
        "inglês": "en",
        "ingles": "en",
        "japonês": "ja",
        "japones": "ja",
        "alemão": "de",
        "alemao": "de",
        "coreano": "ko",
        "espanhol": "es",
        "francês": "fr",
        "frances": "fr",
        "italiano": "it",
        "mandarim": "zh",
        "chinês": "zh",
        "chines": "zh",
        "português": "pt",
        "portugues": "pt",
    }

    def __init__(self, recognizer=None, tts=None):
        self.recognizer = recognizer or LocalSpeechRecognizer()
        self.tts = tts or LocalTTS()

    def preload(self):
        """Pré-carrega voz e reconhecimento para reduzir a primeira latência."""
        tts_ready = self.tts.preload()
        whisper_ready = False
        try:
            whisper_ready = self.recognizer.preload()
        except Exception as exc:
            print(f"[Voz local] Não foi possível pré-carregar o Whisper: {exc}")
        return tts_ready and whisper_ready

    @staticmethod
    def _has_voice(data: np.ndarray, threshold: int = 300) -> bool:
        return bool(data.size and int(np.abs(data).max()) >= threshold)

    def _transcribe(self, data: np.ndarray, sample_rate: int, language="pt"):
        wav_io = pcm_to_wav_bytes(data, sample_rate)
        text, detected_language = self.recognizer.transcribe_wav(
            wav_io,
            language=language,
        )
        if text:
            print(f"[Ouvido local/{detected_language or language}] {text}")
        return text

    def listen(self):
        """Grava apenas enquanto ALT está premido e reconhece a fala localmente."""
        print("[Microfone] A GRAVAR! Solte o ALT quando terminar.")
        try:
            sample_rate = 16000
            recording = sd.rec(
                int(30 * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
            )
            started_at = time.time()
            while keyboard.is_pressed("alt") and time.time() - started_at < 29:
                time.sleep(0.01)
            sd.stop()

            duration = time.time() - started_at
            if duration < 0.3:
                return None
            audio = recording[: int(duration * sample_rate)]
            if not self._has_voice(audio):
                print("[Microfone] Não foi detetada voz com volume suficiente.")
                return ""

            print("[Microfone] A reconhecer localmente...")
            return self._transcribe(audio, sample_rate, language="pt")
        except Exception as exc:
            print(f"Erro no microfone PTT: {type(exc).__name__}: {exc}")
            return ""

    def listen_continuous(self, duration=5):
        """Escuta um bloco de áudio para o modo professora."""
        print(f"[Professora] A escutar localmente ({duration}s)...")
        try:
            sample_rate = 16000
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            if not self._has_voice(recording):
                return ""
            return self._transcribe(recording, sample_rate, language=None)
        except Exception as exc:
            print(f"[Professora] Falha no reconhecimento local: {exc}")
            return ""

    def start_wake_word_listener(self, on_wake_word, is_busy_func):
        """Ouve contínua e levemente em background até detetar 'Ei Siri' ou 'Ei Cortex'."""
        self.wake_word_active = True
        
        def listener_thread():
            sample_rate = 16000
            print("[Mãos-Livres] A aguardar pela palavra mágica ('Ei Cortex' ou 'Ei Siri')...")
            
            # Wake words to look for
            wake_words = [
                "ei siri", "hey siri", "ei cortex", "hey cortex", 
                "ouvir siri", "ouvir cortex", "i siri", "e ai siri", "e ai cortex"
            ]
            
            while getattr(self, "wake_word_active", True):
                if is_busy_func():
                    # Se a Cortex já está a falar ou a processar, fazemos uma pausa para não se ouvir a si própria
                    time.sleep(0.5)
                    continue
                    
                try:
                    # Grava pacotes curtos de 2 segundos para apanhar apenas a ativação
                    recording = sd.rec(int(2.5 * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
                    sd.wait()
                    
                    if not self._has_voice(recording, threshold=250):
                        continue
                        
                    # Transcreve instantaneamente o pequeno pacote de áudio
                    text = self._transcribe(recording, sample_rate, language="pt")
                    if not text:
                        continue
                        
                    text_lower = text.lower()
                    
                    import unicodedata
                    import string
                    normalized_text = unicodedata.normalize('NFKD', text_lower).encode('ASCII', 'ignore').decode('utf-8')
                    clean_text = normalized_text.translate(str.maketrans('', '', string.punctuation))
                    
                    ww_detected = None
                    for ww in wake_words:
                        if ww in clean_text:
                            ww_detected = ww
                            break
                            
                    if ww_detected:
                        print(f"[Mãos-Livres] Wake word '{ww_detected}' detetado!")
                        # Avisa a UI que detetou o wake word para fazer a animação!
                        on_wake_word("WAKE_WORD_ACTIVATED")
                        
                        # Agora ouve o comando real (5 segundos)
                        cmd_recording = sd.rec(int(5 * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
                        sd.wait()
                        
                        cmd_text = self._transcribe(cmd_recording, sample_rate, language="pt")
                        if cmd_text:
                            on_wake_word(cmd_text)
                        else:
                            # Se não disse nada depois, cancelamos
                            on_wake_word("WAKE_WORD_CANCELLED")
                        
                except Exception as exc:
                    print(f"[Mãos-Livres] Erro no loop: {exc}")
                    time.sleep(1)

        threading.Thread(target=listener_thread, daemon=True).start()

    def speak(self, text, callback=None, force_language=None):
        if not text:
            if callback:
                callback()
            return
        clean_text = re.sub(r"[*#`]", "", str(text)).strip()
        language = "pt"
        if force_language:
            language = self.LANGUAGE_CODES.get(force_language.casefold(), "pt")
        try:
            self.tts.speak(clean_text, language)
        except Exception as exc:
            print(f"Erro na voz local: {exc}")
        finally:
            if callback:
                callback()

    def speak_stream(self, text_iterator, callback=None, force_language=None):
        language = "pt"
        if force_language:
            language = self.LANGUAGE_CODES.get(force_language.casefold(), "pt")
            
        buffer = ""
        full_response = ""
        
        try:
            for chunk in text_iterator:
                clean_chunk = re.sub(r"[*#`]", "", str(chunk))
                buffer += clean_chunk
                full_response += clean_chunk
                
                # Se encontrarmos pontuação forte, enviamos para falar
                if any(p in buffer for p in [".", "!", "?", "\n", ":"]):
                    if buffer.strip():
                        try:
                            self.tts.speak(buffer.strip(), language)
                        except Exception as exc:
                            print(f"Erro na voz local (stream): {exc}")
                    buffer = ""
            
            # Fala o que sobrar no buffer
            if buffer.strip():
                try:
                    self.tts.speak(buffer.strip(), language)
                except Exception as exc:
                    print(f"Erro na voz local (stream final): {exc}")
                    
        finally:
            if callback:
                callback()
        
        return full_response

    def generate_speech_file(self, text, language="pt"):
        """Compatibilidade com a interface Eel: cria um WAV local temporário."""
        output_path = os.path.abspath(f"temp_speech_{uuid.uuid4().hex}.wav")
        try:
            return self.tts.synthesize_wave_file(str(text), output_path, language)
        except Exception as exc:
            print(f"Erro ao gerar ficheiro de voz local: {exc}")
            return None
