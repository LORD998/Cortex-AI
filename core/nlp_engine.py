import json
import re
import time
from typing import Any

import requests

from core.config import CortexConfig

class NLPEngine:
    def __init__(self, model_name: str | None = None, config: CortexConfig | None = None):
        self.config = config or CortexConfig.from_env()
        self.api_url = f"{self.config.ollama_url}/api/chat"
        self.health_url = self.config.ollama_url
        self.model_name = model_name or self.config.chat_model
        self._availability_cache = None
        self._availability_checked_at = 0.0
        self._session = requests.Session()
        print(f"[Motor Lógico] Inicializado com {self.model_name} (Ollama local)")

    def is_available(self):
        now = time.monotonic()
        if (
            self._availability_cache is not None
            and now - self._availability_checked_at < 5.0
        ):
            return self._availability_cache
        try:
            response = self._session.get(self.health_url, timeout=2)
            response.raise_for_status()
            available = True
        except requests.RequestException:
            available = False
        self._availability_cache = available
        self._availability_checked_at = now
        return available

    @staticmethod
    def _normalize_tool_calls(message: dict[str, Any]) -> dict[str, Any]:
        """Normaliza argumentos que alguns modelos devolvem como texto JSON."""
        for tool_call in message.get("tool_calls", []) or []:
            function = tool_call.get("function", {})
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    function["arguments"] = json.loads(arguments)
                except json.JSONDecodeError:
                    function["arguments"] = {}
        return message

    def process_with_tools(
        self,
        messages: list,
        tools: list | None = None,
        think: bool = False,
    ):
        """Envia um pedido de chat ao Ollama e devolve uma mensagem normalizada."""
        if not self.is_available():
            return {"role": "assistant", "content": "Servidor Ollama inativo."}

        temperature = 0.25 if tools else 0.4
        max_tokens = 700 if think else (768 if tools else 1024)
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "think": bool(think),
            "keep_alive": "30m",
            "options": {
                "num_ctx": self.config.context_size,
                "num_predict": max_tokens,
                "num_batch": 512,
                "temperature": temperature,
                "top_p": 0.9,
                "repeat_penalty": 1.08,
            }
        }

        if tools:
            payload["tools"] = tools

        try:
            response = self._session.post(
                self.api_url,
                json=payload,
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()
            data = response.json()
            message = self._normalize_tool_calls(data.get("message", {}))

            content = message.get("content", "")
            if content and "<think>" in content:
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                message["content"] = content

            if not message.get("content") and not message.get("tool_calls"):
                message["content"] = "Não consegui formar uma resposta útil. Podes reformular?"

            message.setdefault("role", "assistant")
            return message
        except requests.exceptions.Timeout:
            return {"role": "assistant", "content": "O cérebro demorou demasiado tempo a pensar. Tenta de novo."}
        except requests.exceptions.ConnectionError:
            self._availability_cache = False
            self._availability_checked_at = time.monotonic()
            return {"role": "assistant", "content": "Não consigo ligar-me ao servidor Ollama. Verifica se está a correr."}
        except requests.exceptions.HTTPError as exc:
            detail = exc.response.text[:300] if exc.response is not None else str(exc)
            return {"role": "assistant", "content": f"O Ollama recusou o pedido: {detail}"}
        except Exception as e:
            return {"role": "assistant", "content": f"Falha técnica: {str(e)}"}
