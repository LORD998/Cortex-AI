import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(minimum, min(value, maximum))


def _env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(minimum, min(value, maximum))


@dataclass(frozen=True)
class CortexConfig:
    """Configuração central da Cortex, alterável por variáveis de ambiente."""

    ollama_url: str
    chat_model: str
    vision_model: str
    context_size: int
    request_timeout: int
    max_agent_steps: int
    max_history_messages: int
    max_tools_per_request: int
    reasoning_mode: str
    local_only: bool
    confirm_risky_actions: bool
    language: str
    whisper_model: str
    whisper_device: str
    tts_engine: str
    tts_voice_pt: str
    tts_voice_en: str
    tts_speed: float
    translator_target: str

    @classmethod
    def from_env(cls) -> "CortexConfig":
        base_url = os.getenv("CORTEX_OLLAMA_URL", "http://localhost:11434").rstrip("/")
        return cls(
            ollama_url=base_url,
            chat_model=os.getenv("CORTEX_MODEL", "qwen3:8b"),
            vision_model=os.getenv("CORTEX_VISION_MODEL", "qwen3-vl:8b"),
            context_size=_env_int("CORTEX_CONTEXT_SIZE", 8192, 2048, 32768),
            request_timeout=_env_int("CORTEX_REQUEST_TIMEOUT", 300, 30, 900),
            max_agent_steps=_env_int("CORTEX_MAX_AGENT_STEPS", 6, 1, 15),
            max_history_messages=_env_int("CORTEX_MAX_HISTORY", 24, 6, 60),
            max_tools_per_request=_env_int("CORTEX_MAX_TOOLS", 18, 4, 30),
            reasoning_mode=os.getenv("CORTEX_REASONING", "auto").casefold(),
            local_only=_env_bool("CORTEX_LOCAL_ONLY", True),
            confirm_risky_actions=_env_bool("CORTEX_CONFIRM_RISKY_ACTIONS", False),
            language=os.getenv("CORTEX_LANGUAGE", "pt-BR"),
            whisper_model=os.getenv("CORTEX_WHISPER_MODEL", "small"),
            whisper_device=os.getenv("CORTEX_WHISPER_DEVICE", "auto").casefold(),
            tts_engine=os.getenv("CORTEX_TTS_ENGINE", "kokoro").casefold(),
            tts_voice_pt=os.getenv(
                "CORTEX_TTS_VOICE_PT",
                "pf_dora:0.72,af_heart:0.28",
            ),
            tts_voice_en=os.getenv("CORTEX_TTS_VOICE_EN", "af_heart"),
            tts_speed=_env_float("CORTEX_TTS_SPEED", 1.0, 0.75, 1.25),
            translator_target=os.getenv("CORTEX_TRANSLATOR_TARGET", "en"),
        )
