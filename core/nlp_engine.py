import requests
import json
import re

class NLPEngine:
    def __init__(self, model_name="qwen3:8b"):
        self.api_url = "http://localhost:11434/api/chat"
        self.model_name = model_name
        print(f"[Motor Lógico] Inicializado com {model_name} (Acesso Local)")

    def is_available(self):
        try:
            requests.get("http://localhost:11434", timeout=2)
            return True
        except:
            return False

    def process_with_tools(self, messages: list, tools: list = None):
        """Envia um pedido de chat ao Ollama."""
        if not self.is_available():
            return {"role": "assistant", "content": "Servidor Ollama inativo."}
        
        # O Qwen3 usa um modo de raciocínio avançado (Chain-of-Thought) dentro da tag <think>.
        # Vamos permitir que ele pense, mas extrair apenas a resposta final para a voz.
        processed_messages = messages
            
        payload = {
            "model": self.model_name,
            "messages": processed_messages,
            "stream": False,
            "keep_alive": -1,
            "options": {
                "num_ctx": 4096,       # Reduzido para metade: acelera drasticamente a leitura do contexto inicial
                "temperature": 0.5,
                "top_p": 0.9,
                "num_gpu": 99          # Força a usar a gráfica ao máximo
                # Removido o num_thread forçado para o Ollama otimizar automaticamente conforme o CPU dele
            }
        }
        
        if tools:
            payload["tools"] = tools
            
        try:
            response = requests.post(self.api_url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            message = data.get("message", {})
            
            # Limpar tags <think> residuais caso ainda apareçam
            content = message.get("content", "")
            if content and "<think>" in content:
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                message["content"] = content
            
            # Se o conteúdo ficou vazio após limpeza e não há tool_calls, dar resposta genérica
            if not message.get("content") and not message.get("tool_calls"):
                message["content"] = "Entendido. Diz-me o que precisas."
            
            return message
        except requests.exceptions.Timeout:
            return {"role": "assistant", "content": "O cérebro demorou demasiado tempo a pensar. Tenta de novo."}
        except requests.exceptions.ConnectionError:
            return {"role": "assistant", "content": "Não consigo ligar-me ao servidor Ollama. Verifica se está a correr."}
        except Exception as e:
            return {"role": "assistant", "content": f"Falha técnica: {str(e)}"}

