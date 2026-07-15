import pyautogui
import time
import pyperclip

class KeyboardManager:
    def __init__(self):
        # Configurar pausa de segurança
        pyautogui.PAUSE = 0.05
        
    def digitar_texto(self, texto: str):
        """Usa a área de transferência para colar texto rapidamente, evitando problemas com acentos."""
        try:
            print("[KeyboardManager] A preparar para digitar texto...")
            
            # Guardar o que estava antes no clipboard
            clipboard_antigo = pyperclip.paste()
            
            # Copiar o novo texto para a área de transferência
            pyperclip.copy(texto)
            
            # Pequena pausa para garantir que o utilizador está na janela certa
            time.sleep(0.5)
            
            # Simular CTRL+V
            pyautogui.hotkey('ctrl', 'v')
            
            # Restaurar a área de transferência (opcional, mas educado)
            time.sleep(0.1)
            pyperclip.copy(clipboard_antigo)
            
            return f"Texto digitado fisicamente com sucesso na janela atual:\n{texto[:50]}..."
        except Exception as e:
            return f"Erro ao tentar digitar no teclado: {str(e)}"

    def press_hotkey(self, keys: str):
        """Simula a pressão de atalhos de teclado (ex: 'ctrl+w' para fechar aba, 'enter', 'tab')."""
        try:
            print(f"[KeyboardManager] A pressionar teclas: {keys}")
            key_list = [k.strip() for k in keys.split('+')]
            pyautogui.hotkey(*key_list)
            return f"Atalho '{keys}' pressionado com sucesso."
        except Exception as e:
            return f"Erro ao pressionar atalho '{keys}': {str(e)}"

    def segurar_tecla(self, tecla: str, segundos: float):
        """Segura uma tecla física pressionada durante X segundos. Ótimo para videojogos (ex: andar no Roblox)."""
        try:
            print(f"[KeyboardManager] A segurar '{tecla}' durante {segundos}s...")
            pyautogui.keyDown(tecla)
            time.sleep(segundos)
            pyautogui.keyUp(tecla)
            return f"Tecla '{tecla}' segurada por {segundos} segundos com sucesso."
        except Exception as e:
            pyautogui.keyUp(tecla) # Fail-safe
            return f"Erro ao segurar tecla '{tecla}': {str(e)}"
            
    def mover_rato(self, x: int, y: int):
        """Move o rato fisicamente para as coordenadas exatas do ecrã (X, Y)."""
        try:
            print(f"[KeyboardManager] A mover o rato para ({x}, {y})...")
            pyautogui.moveTo(x, y, duration=0.5)
            return f"Rato movido para as coordenadas X:{x}, Y:{y} com sucesso."
        except Exception as e:
            return f"Erro ao mover o rato: {str(e)}"

    def clicar_rato(self, botao: str = 'left', duplo: bool = False):
        """Simula um clique do rato (esquerdo, direito ou meio) para interagir com o ecrã/jogos."""
        try:
            print(f"[KeyboardManager] A clicar no rato ({botao})...")
            if duplo:
                pyautogui.doubleClick(button=botao)
                return f"Duplo-clique '{botao}' executado."
            else:
                pyautogui.click(button=botao)
                return f"Clique '{botao}' executado."
        except Exception as e:
            return f"Erro ao clicar com o rato: {str(e)}"
