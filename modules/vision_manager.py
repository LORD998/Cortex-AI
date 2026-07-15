import base64
from io import BytesIO
import requests
from PIL import ImageGrab

class VisionManager:
    def __init__(self):
        self.api_url = "http://localhost:11434/api/chat"
        self.model_name = "qwen3-vl:8b"  # Usar qwen3-vl para suportar OCR perfeito e PT-PT nativo sem hacks de tradução
        print(f"[Córtex Visual] A usar {self.model_name} como modelo visual")

    def analisar_ecra(self, pergunta: str = "Descreve detalhadamente o que vês no ecrã e onde estão as coisas."):
        """Tira print e envia para o qwen3-vl para interpretação nativa."""
        try:
            from PIL import ImageGrab
            import io, base64, requests
            print("[Córtex Visual] A usar qwen3-vl:8b como modelo visual nativo...")
            
            # 1. Tirar print
            print("[Córtex Visual] A tirar captura fotográfica do ecrã...")
            img = ImageGrab.grab(all_screens=True)
            
            # Redimensionar para 720p para evitar lentidão extrema
            img.thumbnail((1280, 720))
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # 2. Enviar para Qwen3-VL com prompt nativo PT-PT (sem tradução necessária)
            print(f"[Córtex Visual] A analisar imagem (qwen3-vl:8b) com a pergunta: '{pergunta}'")
            payload = {
                "model": "qwen3-vl:8b",
                "prompt": f"Responde EXATAMENTE em Português de Portugal (PT-PT) à seguinte pergunta sobre a imagem. Se a pergunta pedir a localização de algo, diz-me a área do ecrã.\nPergunta: {pergunta}",
                "images": [img_str],
                "stream": False,
                "options": {
                    "num_ctx": 4096,
                    "temperature": 0.2
                }
            }
            
            # Aumentei o timeout para 180s porque modelos VL pesados demoram a carregar para a VRAM
            response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=180)
            response.raise_for_status()
            resultado = response.json().get("response", "Erro ao processar imagem.")
            
            # Limpar tags <think> do Qwen3 caso existam
            if "<think>" in resultado:
                import re
                resultado = re.sub(r'<think>.*?</think>', '', resultado, flags=re.DOTALL).strip()
            
            print("[Córtex Visual] Visão concluída.")
            return resultado.strip()
            
        except requests.exceptions.Timeout:
            return "Erro: O modelo visual demorou demasiado tempo a responder (Timeout de 180s). Tenta novamente ou fecha programas pesados."
        except Exception as e:
            print(f"Erro Visual: {e}")
            return f"Erro fatal do sistema de visão: {str(e)}"
