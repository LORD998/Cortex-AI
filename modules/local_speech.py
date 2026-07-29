import base64
import io
import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path

from core.config import CortexConfig


class LocalSpeechRecognizer:
    """Reconhecimento de voz offline com faster-whisper, carregado sob demanda."""

    def __init__(self, model_size: str | None = None):
        self.config = CortexConfig.from_env()
        self.model_size = model_size or self.config.whisper_model
        self.device = self.config.whisper_device
        self._model = None
        self._active_device = None
        self._lock = threading.Lock()
        self._transcribe_lock = threading.Lock()

    def _create_model(self, device: str):
        from faster_whisper import WhisperModel

        compute_type = "float16" if device == "cuda" else "int8"
        model = WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type,
        )
        self._active_device = device
        return model

    def _load_model(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                import faster_whisper  # noqa: F401
            except ImportError as exc:
                raise RuntimeError(
                    "O reconhecimento local requer 'faster-whisper'. "
                    "Instala as dependências com: pip install -r requirements.txt"
                ) from exc

            requested_device = self.device if self.device in {"cpu", "cuda"} else "cuda"
            try:
                self._model = self._create_model(requested_device)
            except Exception as device_error:
                if requested_device == "cpu":
                    raise
                print(
                    "[Voz local] CUDA indisponível para o Whisper; "
                    f"a usar CPU ({device_error})."
                )
                self._model = self._create_model("cpu")
        return self._model

    def preload(self):
        """Carrega o Whisper em background para a primeira fala não ficar lenta."""
        self._load_model()
        print(
            f"[Voz local] Whisper {self.model_size} pronto "
            f"em {self._active_device or self.device}."
        )
        return True

    def transcribe_wav(self, wav_source, language: str | None = None):
        with self._transcribe_lock:
            model = self._load_model()
            if hasattr(wav_source, "seek"):
                wav_source.seek(0)

            def transcribe(active_model):
                return active_model.transcribe(
                    wav_source,
                    language=language,
                    beam_size=4,
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 300},
                    condition_on_previous_text=False,
                )

            try:
                segments, info = transcribe(model)
                segments = list(segments)
            except RuntimeError as exc:
                if self._active_device != "cuda":
                    raise
                print(f"[Voz local] Falha no runtime CUDA; a mudar para CPU ({exc}).")
                with self._lock:
                    self._model = self._create_model("cpu")
                if hasattr(wav_source, "seek"):
                    wav_source.seek(0)
                segments, info = transcribe(self._model)
                segments = list(segments)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        detected_language = getattr(info, "language", language or "")
        return text, detected_language


class LocalTTS:
    """Voz neural local rápida, com Kokoro e SAPI como alternativas."""

    _kokoro = None
    _kokoro_key = None
    _kokoro_lock = threading.Lock()
    _piper = None
    _piper_key = None
    _piper_lock = threading.Lock()
    _audio_lock = threading.Lock()

    _SPEAK_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$text = [Text.Encoding]::UTF8.GetString(
    [Convert]::FromBase64String($env:CORTEX_TTS_TEXT_B64)
)
$language = $env:CORTEX_TTS_LANGUAGE
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($language) {
    $voice = $speaker.GetInstalledVoices() |
        Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name.StartsWith($language) } |
        Select-Object -First 1
    if ($voice) { $speaker.SelectVoice($voice.VoiceInfo.Name) }
}
$speaker.Speak($text)
$speaker.Dispose()
"""

    def __init__(self):
        self.config = CortexConfig.from_env()
        project_root = Path(__file__).resolve().parents[1]
        self.model_path = project_root / "assets" / "tts" / "kokoro-v1.0.int8.onnx"
        self.voices_path = project_root / "assets" / "tts" / "voices-v1.0.bin"
        self.piper_model_path = (
            project_root / "assets" / "tts" / "pt_PT-tugao-medium.onnx"
        )
        self.piper_config_path = (
            project_root / "assets" / "tts" / "pt_PT-tugao-medium.onnx.json"
        )

    def _voice_profile(self, language: str):
        language = (language or "pt").casefold().split("-")[0]
        profiles = {
            "pt": (self.config.tts_voice_pt, "pt-br"),
            "en": (self.config.tts_voice_en, "en-us"),
            "es": ("ef_dora", "es"),
            "fr": ("ff_siwis", "fr-fr"),
            "it": ("if_sara", "it"),
            "ja": ("jf_alpha", "ja"),
            "zh": ("zf_xiaoxiao", "cmn"),
        }
        return profiles.get(language)

    def _load_kokoro(self):
        if not self.model_path.is_file() or not self.voices_path.is_file():
            raise FileNotFoundError(
                "Faltam os modelos da voz neural em assets/tts. "
                "Executa scripts/setup_local_voice.py."
            )

        key = (str(self.model_path), str(self.voices_path))
        if self.__class__._kokoro is not None and self.__class__._kokoro_key == key:
            return self.__class__._kokoro

        with self.__class__._kokoro_lock:
            if self.__class__._kokoro is None or self.__class__._kokoro_key != key:
                from kokoro_onnx import Kokoro

                self.__class__._kokoro = Kokoro(*key)
                self.__class__._kokoro_key = key
        return self.__class__._kokoro

    def _load_piper(self):
        if not self.piper_model_path.is_file() or not self.piper_config_path.is_file():
            raise FileNotFoundError(
                "Falta a voz Piper portuguesa em assets/tts. "
                "Executa scripts/setup_local_voice.py."
            )
        key = (str(self.piper_model_path), str(self.piper_config_path))
        if self.__class__._piper is not None and self.__class__._piper_key == key:
            return self.__class__._piper

        with self.__class__._piper_lock:
            if self.__class__._piper is None or self.__class__._piper_key != key:
                import json

                import onnxruntime as ort
                from piper import PiperVoice
                from piper.config import PiperConfig

                providers = ["CPUExecutionProvider"]
                available = ort.get_available_providers()
                if "DmlExecutionProvider" in available:
                    providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
                options = ort.SessionOptions()
                options.log_severity_level = 3
                session = ort.InferenceSession(
                    str(self.piper_model_path),
                    sess_options=options,
                    providers=providers,
                )
                with self.piper_config_path.open("r", encoding="utf-8") as handle:
                    voice_config = PiperConfig.from_dict(json.load(handle))
                self.__class__._piper = PiperVoice(session, voice_config)
                self.__class__._piper_key = key
        return self.__class__._piper

    def preload(self):
        """Carrega a voz neural antes de ela ser necessária."""
        try:
            if self.config.tts_engine == "piper":
                voice = self._load_piper()
                provider = voice.session.get_providers()[0]
                print(
                    f"[Voz neural] Piper pt-PT pronto em {provider}, "
                    f"velocidade {self.config.tts_speed:.2f}."
                )
                return True
            self._load_kokoro()
            print(
                f"[Voz neural] Kokoro pronto: {self.config.tts_voice_pt}, "
                f"velocidade {self.config.tts_speed:.2f}."
            )
            return True
        except Exception as exc:
            print(f"[Voz neural] Motor neural indisponível; SAPI será usado: {exc}")
            return False

    def _piper_config(self):
        from piper import SynthesisConfig

        return SynthesisConfig(
            length_scale=1.0 / self.config.tts_speed,
            noise_scale=0.58,
            noise_w_scale=0.72,
            normalize_audio=True,
            volume=0.92,
        )

    def _piper_chunks(self, text: str):
        voice = self._load_piper()
        return voice.synthesize(text, self._piper_config())

    def _synthesize_piper(self, text: str):
        import numpy as np

        chunks = list(self._piper_chunks(text))
        if not chunks:
            raise RuntimeError("A voz Piper não produziu áudio.")
        sample_rate = chunks[0].sample_rate
        audio = np.concatenate(
            [
                np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
                for chunk in chunks
            ]
        )
        return audio.astype(np.float32) / 32768.0, sample_rate

    def _speak_piper_streaming(self, text: str):
        import queue

        import sounddevice as sd

        chunks = queue.Queue(maxsize=3)
        finished = object()

        def producer():
            try:
                for chunk in self._piper_chunks(text):
                    chunks.put(chunk)
            except Exception as exc:
                chunks.put(exc)
            finally:
                chunks.put(finished)

        worker = threading.Thread(target=producer, daemon=True)
        worker.start()
        first = chunks.get(timeout=60)
        if isinstance(first, Exception):
            raise first
        if first is finished:
            raise RuntimeError("A voz Piper não produziu áudio.")

        with sd.RawOutputStream(
            samplerate=first.sample_rate,
            channels=first.sample_channels,
            dtype="int16",
        ) as output:
            output.write(first.audio_int16_bytes)
            while True:
                item = chunks.get(timeout=60)
                if item is finished:
                    break
                if isinstance(item, Exception):
                    raise item
                output.write(item.audio_int16_bytes)
        worker.join(timeout=1)

    @staticmethod
    def _chunks(text: str, max_chars: int = 320):
        sentences = [
            part.strip()
            for part in re.split(r"(?<=[.!?;:])\s+", text.strip())
            if part.strip()
        ]
        chunks = []
        current = ""
        for sentence in sentences:
            if len(sentence) > max_chars:
                words = sentence.split()
                for word in words:
                    candidate = f"{current} {word}".strip()
                    if current and len(candidate) > max_chars:
                        chunks.append(current)
                        current = word
                    else:
                        current = candidate
                continue
            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks or [text]

    def _synthesize_neural(self, text: str, language: str):
        import numpy as np

        profile = self._voice_profile(language)
        if profile is None:
            raise ValueError(f"Kokoro não possui uma voz configurada para {language}.")
        voice, phoneme_language = profile
        kokoro = self._load_kokoro()
        audio_parts = []
        sample_rate = 24000

        for chunk in self._chunks(text):
            samples, sample_rate = kokoro.create(
                chunk,
                voice=voice,
                speed=self.config.tts_speed,
                lang=phoneme_language,
            )
            samples = np.asarray(samples, dtype=np.float32).reshape(-1)
            if samples.size:
                peak = float(np.max(np.abs(samples)))
                if peak > 0.96:
                    samples *= 0.96 / peak
                fade = min(int(sample_rate * 0.012), samples.size // 2)
                if fade:
                    curve = np.linspace(0.0, 1.0, fade, dtype=np.float32)
                    samples[:fade] *= curve
                    samples[-fade:] *= curve[::-1]
                audio_parts.append(samples)
                audio_parts.append(np.zeros(int(sample_rate * 0.065), dtype=np.float32))

        if not audio_parts:
            raise RuntimeError("A voz neural não produziu áudio.")
        return np.concatenate(audio_parts[:-1]), sample_rate

    _WAVE_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$text = [Text.Encoding]::UTF8.GetString(
    [Convert]::FromBase64String($env:CORTEX_TTS_TEXT_B64)
)
$path = [Text.Encoding]::UTF8.GetString(
    [Convert]::FromBase64String($env:CORTEX_TTS_PATH_B64)
)
$language = $env:CORTEX_TTS_LANGUAGE
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($language) {
    $voice = $speaker.GetInstalledVoices() |
        Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name.StartsWith($language) } |
        Select-Object -First 1
    if ($voice) { $speaker.SelectVoice($voice.VoiceInfo.Name) }
}
$speaker.SetOutputToWaveFile($path)
$speaker.Speak($text)
$speaker.Dispose()
"""

    @staticmethod
    def _encoded_command(script: str) -> str:
        return base64.b64encode(script.encode("utf-16le")).decode("ascii")

    @staticmethod
    def _env(text: str, language: str, path: str | None = None):
        env = os.environ.copy()
        env["CORTEX_TTS_TEXT_B64"] = base64.b64encode(
            text.encode("utf-8")
        ).decode("ascii")
        env["CORTEX_TTS_LANGUAGE"] = language or ""
        if path:
            env["CORTEX_TTS_PATH_B64"] = base64.b64encode(
                path.encode("utf-8")
            ).decode("ascii")
        return env

    @staticmethod
    def _run(script: str, env: dict):
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                LocalTTS._encoded_command(script),
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
            creationflags=creation_flags,
            check=False,
        )

    def _sapi_speak(self, text: str, language: str = "pt"):
        if not text.strip():
            return
        result = self._run(
            self._SPEAK_SCRIPT,
            self._env(text, language),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Falha na voz SAPI.")

    def _sapi_wave_bytes(self, text: str, language: str = "pt") -> bytes:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
                temp_path = handle.name
            result = self._run(
                self._WAVE_SCRIPT,
                self._env(text, language, temp_path),
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Falha na voz SAPI.")
            with open(temp_path, "rb") as handle:
                return handle.read()
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _sapi_wave_file(
        self,
        text: str,
        output_path: str,
        language: str = "pt",
    ) -> str:
        result = self._run(
            self._WAVE_SCRIPT,
            self._env(text, language, output_path),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Falha na voz SAPI.")
        return output_path

    _EMOJI_RE = re.compile(
        "["
        "\U0001F1E6-\U0001F1FF"  # bandeiras
        "\U0001F300-\U0001FAFF"  # emoji, pictogramas, símbolos suplementares
        "\U00002600-\U000027BF"  # símbolos diversos, dingbats
        "\U00002B00-\U00002BFF"  # setas e símbolos diversos
        "\U0000FE0F"  # seletor de variação (emoji presentation)
        "\U0000200D"  # zero-width joiner (emoji compostos)
        "]+",
        flags=re.UNICODE,
    )

    @classmethod
    def _sanitize_for_speech(cls, text: str) -> str:
        cleaned = cls._EMOJI_RE.sub("", text)
        return re.sub(r"[ \t]{2,}", " ", cleaned).strip()

    def speak(self, text: str, language: str = "pt"):
        text = self._sanitize_for_speech(text)
        if not text.strip():
            return
        try:
            with self.__class__._audio_lock:
                if (
                    self.config.tts_engine == "piper"
                    and (language or "pt").casefold().startswith("pt")
                ):
                    self._speak_piper_streaming(text)
                else:
                    import sounddevice as sd

                    samples, sample_rate = self._synthesize_neural(text, language)
                    sd.play(samples, sample_rate)
                    sd.wait()
        except Exception as neural_error:
            print(f"[Voz neural] A usar fallback SAPI: {neural_error}")
            self._sapi_speak(text, language)

    def synthesize_wave_bytes(self, text: str, language: str = "pt") -> bytes:
        text = self._sanitize_for_speech(text)
        try:
            import soundfile as sf

            if (
                self.config.tts_engine == "piper"
                and (language or "pt").casefold().startswith("pt")
            ):
                samples, sample_rate = self._synthesize_piper(text)
            else:
                samples, sample_rate = self._synthesize_neural(text, language)
            output = io.BytesIO()
            sf.write(output, samples, sample_rate, format="WAV", subtype="PCM_16")
            output.seek(0)
            return output.read()
        except Exception as neural_error:
            print(f"[Voz neural] WAV via SAPI: {neural_error}")
            return self._sapi_wave_bytes(text, language)

    def synthesize_wave_file(
        self,
        text: str,
        output_path: str,
        language: str = "pt",
    ) -> str:
        text = self._sanitize_for_speech(text)
        try:
            import soundfile as sf

            if (
                self.config.tts_engine == "piper"
                and (language or "pt").casefold().startswith("pt")
            ):
                samples, sample_rate = self._synthesize_piper(text)
            else:
                samples, sample_rate = self._synthesize_neural(text, language)
            sf.write(output_path, samples, sample_rate, subtype="PCM_16")
            return output_path
        except Exception as neural_error:
            print(f"[Voz neural] Ficheiro via SAPI: {neural_error}")
            return self._sapi_wave_file(text, output_path, language)

    @staticmethod
    def stop():
        try:
            import sounddevice as sd

            sd.stop()
        except Exception:
            pass


def pcm_to_wav_bytes(data, sample_rate: int) -> io.BytesIO:
    import wave

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(data.tobytes())
    wav_io.seek(0)
    return wav_io
