"""Atalhos locais para comandos determinísticos que não precisam do LLM.

Cobre apenas pedidos inequívocos (hora, volume, abrir app conhecida, janelas,
screenshot, media keys). Qualquer coisa ambígua devolve None e cai no
caminho normal (LLM + ferramentas).
"""

import re
import unicodedata


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


_NUMBER_RE = re.compile(r"\b(\d{1,3})\b")

_TIME_RE = re.compile(r"\b(que horas|que dia (e|era)|data de hoje|dia de hoje)\b")
_SCREENSHOT_RE = re.compile(r"\b(tira|faz|captura)\b.*\b(screenshot|captura de ecra|print)\b")
_MINIMIZE_ALL_RE = re.compile(
    r"\b(minimiza(r)? tudo|mostra(r)? (o )?ambiente de trabalho|mostra(r)? (a )?area de trabalho)\b"
)
_OPEN_RE = re.compile(r"\b(abre|abrir|lanca|lancar|inicia|iniciar)\b\s+(?:o|a|os|as)?\s*(.+)")
_MINIMIZE_WIN_RE = re.compile(r"\bminimiza(r)?\b\s+(?:o|a)?\s*(.+)")
_MAXIMIZE_WIN_RE = re.compile(r"\bmaximiza(r)?\b\s+(?:o|a)?\s*(.+)")

_VOLUME_MUTE_RE = re.compile(r"\b(muta|silencia)\b.*\b(som|volume|audio)\b|\b(muta|silencia)\b$")
_VOLUME_MAX_RE = re.compile(r"\bvolume\b.*\b(maximo|no maximo)\b")
_VOLUME_SET_RE = re.compile(r"\bvolume\b")

_MEDIA_PATTERNS = (
    (re.compile(r"\b(pausa|para)\b.*\b(musica|reproducao)\b|\bpausa\b$"), "play_pause"),
    (re.compile(r"\b(continua|retoma|toca)\b.*\b(musica|reproducao)\b"), "play_pause"),
    (re.compile(r"\b(proxima|avanca)\b.*\b(musica|faixa)\b"), "next"),
    (re.compile(r"\b(musica|faixa)\b.*\banterior\b|\bvolta\b.*\bfaixa\b"), "previous"),
)


def try_fast_intent(command: str, modules: dict):
    """Tenta resolver o comando localmente. Devolve texto de resposta ou None."""
    text = _normalize(command).strip()
    if not text:
        return None

    os_manager = modules.get("os_manager")
    keyboard_manager = modules.get("keyboard_manager")

    if _TIME_RE.search(text) and os_manager:
        return os_manager.get_current_time()

    if _SCREENSHOT_RE.search(text) and os_manager:
        return os_manager.tirar_screenshot()

    if _MINIMIZE_ALL_RE.search(text) and os_manager:
        return os_manager.minimizar_tudo()

    if os_manager and _VOLUME_MUTE_RE.search(text):
        return os_manager.ajustar_volume(0)

    if os_manager and _VOLUME_MAX_RE.search(text):
        return os_manager.ajustar_volume(100)

    if os_manager and _VOLUME_SET_RE.search(text):
        match = _NUMBER_RE.search(text)
        if match:
            return os_manager.ajustar_volume(int(match.group(1)))

    if keyboard_manager:
        for pattern, action in _MEDIA_PATTERNS:
            if pattern.search(text):
                return keyboard_manager.media_key(action)

    if os_manager:
        match = _MAXIMIZE_WIN_RE.search(text)
        if match:
            alvo = match.group(2).strip()
            if alvo:
                return os_manager.maximizar_janela(alvo)

        match = _MINIMIZE_WIN_RE.search(text)
        if match:
            alvo = match.group(2).strip()
            if alvo:
                return os_manager.minimizar_janela(alvo)

        match = _OPEN_RE.search(text)
        if match:
            alvo = match.group(2).strip()
            if alvo in os_manager.app_aliases:
                return os_manager.open_application(alvo)

    return None
