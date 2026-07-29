import sys
import os

# Redirecionar stdout/stderr para evitar crash do pythonw
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
import threading
import subprocess
import math
import time
import requests
from core.config import CortexConfig
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush, QLinearGradient
import keyboard

from core.orchestrator import CortexOrchestrator
from modules.file_manager import FileManager
from modules.os_manager import OSManager
from modules.memory_manager import MemoryManager
from modules.vision_manager import VisionManager
from modules.voice_manager import VoiceManager
from modules.keyboard_manager import KeyboardManager
from modules.web_manager import WebManager
from modules.dev_manager import DevManager
from modules.business_manager import BusinessManager
from modules.data_analysis import DataAnalysis
from modules.email_manager import EmailManager
from modules.web_automation import WebAutomation
from modules.local_speech import LocalSpeechRecognizer, LocalTTS

class SubtitleOverlay(QWidget):
    subtitle_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen_geometry = QApplication.primaryScreen().geometry()
        w = int(screen_geometry.width() * 0.8)
        h = 100
        center_x = screen_geometry.width() // 2
        center_y = screen_geometry.height() - 300
        
        self.setGeometry(center_x - (w // 2), center_y - (h // 2), w, h)
        
        self.label = QLabel("", self)
        self.label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 10px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setGeometry(0, 0, w, h)
        self.label.hide()
        
        self.subtitle_changed.connect(self.update_text)
        
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(lambda: self.update_text(""))
        self.clear_timer.setSingleShot(True)

    def update_text(self, text):
        if text:
            self.label.setText(text)
            self.label.show()
            self.clear_timer.start(10000)
        else:
            self.label.hide()


class EdgeGlowOverlay(QWidget):
    state_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.state = "idle" 
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen_geometry = QApplication.primaryScreen().geometry()
        
        # OTIMIZAÇÃO EXTREMA: Em vez de uma janela transparente do tamanho do ecrã todo (que mata a GPU),
        # a janela vai ter apenas 300x300 pixeis.
        w, h = 300, 300
        # Centrar horizontalmente e colocar na parte inferior (acima da barra de tarefas)
        center_x = screen_geometry.width() // 2
        center_y = screen_geometry.height() - 120
        
        # Posicionar o topo esquerdo do widget para que o seu centro fique no sítio exato
        self.setGeometry(center_x - (w // 2), center_y - (h // 2), w, h)
        
        self.state_changed.connect(self.update_state)
        
        self.glow_intensity = 0
        self.glow_direction = 1
        self.time_offset = 0.0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_glow)
        # 33ms = ~30 FPS (Metade do uso da GPU/CPU comparado com 15ms)
        self.timer.start(33) 
        
    def update_state(self, new_state):
        self.state = new_state
        self._update_orb_area()
        
    def animate_glow(self):
        # Reduzi o incremento para que a bola não gire histericamente rápida
        self.time_offset += 0.03 
        
        # Pulso orgânico mais suave
        self.glow_intensity += 8 * self.glow_direction
        if self.glow_intensity > 255:
            self.glow_direction = -1
        elif self.glow_intensity < 50:
            self.glow_direction = 1
            
        self._update_orb_area()
        
    def _update_orb_area(self):
        """A janela agora tem 300x300. Basta atualizar a janela inteira, não pesa nada."""
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        try:
            # Tema Siri Original (Fitas 3D / Pétalas)
            orb_y = self.height() // 2
            orb_x = self.width() // 2
            
            if self.state == "speaking":
                base_radius = 65 + (math.sin(self.time_offset * 4) * 5)
                speed_mult = 3.0
                opacity_mult = 2.5 # Super vibrante
            elif self.state == "listening":
                base_radius = 50 + (math.sin(self.time_offset * 2) * 3)
                speed_mult = 2.0
                opacity_mult = 1.8 
            elif self.state == "thinking":
                base_radius = 50 + (math.sin(self.time_offset) * 2)
                speed_mult = 1.0
                opacity_mult = 1.5 
            else: # idle
                base_radius = 35
                speed_mult = 0.2
                opacity_mult = 1.0 # Bem visível em idle, sem ficar fosco
                
            # 1. Base Escura da Esfera com Reflexos (Rim Lights) nas bordas
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            # Para imitar a imagem, um gradiente diagonal para a bolha exterior (Azul forte em cima, Rosa forte em baixo)
            rim_grad = QLinearGradient(float(orb_x - base_radius), float(orb_y - base_radius), float(orb_x + base_radius), float(orb_y + base_radius))
            rim_grad.setColorAt(0.0, QColor(0, 200, 255, min(255, int(180 * opacity_mult)))) # Ciano forte topo-esquerdo
            rim_grad.setColorAt(0.5, QColor(0, 0, 0, min(255, int(80 * opacity_mult)))) # Meio escuro para dar contraste
            rim_grad.setColorAt(1.0, QColor(255, 30, 120, min(255, int(180 * opacity_mult)))) # Rosa forte fundo-direito
            painter.setBrush(QBrush(rim_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(int(orb_x), int(orb_y)), int(base_radius), int(base_radius))
            
            # --- MÁGICA DA LUZ ---
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
            
            # 2. As "Fitas" / Pétalas da Siri
            # Cores puras e saturadas
            ribbons = [
                {"color": (0, 220, 255), "angle": 0, "dist": 0.2, "w": 0.9, "h": 0.4},     # Ciano Brilhante
                {"color": (255, 50, 255), "angle": 51, "dist": 0.3, "w": 0.8, "h": 0.5},   # Magenta Puro
                {"color": (255, 60, 40), "angle": 102, "dist": 0.25, "w": 0.8, "h": 0.4},  # Vermelho Alaranjado
                {"color": (50, 255, 150), "angle": 154, "dist": 0.2, "w": 0.7, "h": 0.5},  # Verde Menta
                {"color": (255, 220, 0), "angle": 205, "dist": 0.3, "w": 0.85, "h": 0.45}, # Amarelo Sol
                {"color": (130, 50, 255), "angle": 257, "dist": 0.2, "w": 0.9, "h": 0.4},  # Roxo Elétrico
                {"color": (255, 0, 80), "angle": 308, "dist": 0.25, "w": 0.8, "h": 0.5}    # Rosa Choque
            ]
            
            for i, rib in enumerate(ribbons):
                painter.save()
                painter.translate(orb_x, orb_y)
                
                current_angle = rib["angle"] + (self.time_offset * speed_mult * 15 * (1 if i % 2 == 0 else -1))
                breath = math.sin(self.time_offset * speed_mult * 0.8 + i)
                
                painter.rotate(current_angle)
                
                rx = base_radius * (rib["w"] + breath * 0.1) * 1.05
                ry = base_radius * (rib["h"] - breath * 0.1) * 1.05
                offset_x = base_radius * (rib["dist"] + breath * 0.05)
                
                # Gradiente para cor sólida e rica, não fosca
                grad = QLinearGradient(-rx, 0, rx, 0)
                grad.setColorAt(0.0, QColor(rib["color"][0], rib["color"][1], rib["color"][2], min(255, int(40 * opacity_mult))))   
                grad.setColorAt(0.4, QColor(rib["color"][0], rib["color"][1], rib["color"][2], min(255, int(255 * opacity_mult)))) # Saturação máxima
                grad.setColorAt(0.6, QColor(rib["color"][0], rib["color"][1], rib["color"][2], min(255, int(255 * opacity_mult)))) # Centro da fita sólido
                grad.setColorAt(1.0, QColor(rib["color"][0], rib["color"][1], rib["color"][2], 0))    
                
                painter.setBrush(QBrush(grad))
                painter.drawEllipse(QPointF(offset_x, 0.0), rx, ry)
                
                painter.restore()

            # 3. Núcleo Ofuscante Branco Intenso
            core_rad = base_radius * 0.5 + (math.sin(self.time_offset * speed_mult * 2) * 5)
            core_grad = QRadialGradient(float(orb_x), float(orb_y), float(core_rad))
            core_grad.setColorAt(0.0, QColor(255, 255, 255, 255)) 
            core_grad.setColorAt(0.4, QColor(255, 255, 255, min(255, int(200 * opacity_mult)))) 
            core_grad.setColorAt(1.0, QColor(255, 255, 255, 0))   
            
            painter.setBrush(QBrush(core_grad))
            painter.drawEllipse(QPoint(int(orb_x), int(orb_y)), int(core_rad), int(core_rad))
            
        except Exception as e:
            print(f"ERROR in paintEvent: {e}")
        finally:
            painter.end()


def preload_ollama():
    try:
        config = CortexConfig.from_env()
        try:
            requests.get(config.ollama_url, timeout=2).raise_for_status()
        except requests.RequestException:
            subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(20):
                time.sleep(0.5)
                try:
                    requests.get(config.ollama_url, timeout=1).raise_for_status()
                    break
                except requests.RequestException:
                    continue
            else:
                raise RuntimeError("O servidor Ollama não arrancou em 10 segundos.")

        print(f"[Ollama] A pré-aquecer {config.chat_model}...")
        response = requests.post(
            f"{config.ollama_url}/api/generate",
            json={
                "model": config.chat_model,
                "prompt": "",
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "num_ctx": config.context_size,
                    "num_batch": 512,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        print(f"[Ollama] Cérebro {config.chat_model} carregado com sucesso.")
    except Exception as exc:
        print(f"[Ollama] Não foi possível pré-aquecer o modelo: {exc}")

def start_cortex():
    app = QApplication(sys.argv)
    overlay = EdgeGlowOverlay()
    
    subtitle_overlay = SubtitleOverlay()
    subtitle_overlay.show()
    
    shared_recognizer = LocalSpeechRecognizer()
    shared_tts = LocalTTS()
    
    print("A inicializar os Sistemas Invisíveis Orgânicos da Cortex...")

    threading.Thread(target=preload_ollama, daemon=True).start()
    
    orchestrator = CortexOrchestrator()
    file_manager = FileManager()
    os_manager = OSManager()
    vision_manager = VisionManager()
    memory_manager = MemoryManager()
    keyboard_manager = KeyboardManager()
    web_manager = WebManager()
    
    orchestrator.load_module("file_manager", file_manager)
    orchestrator.load_module("os_manager", os_manager)
    orchestrator.load_module("vision_manager", vision_manager)
    orchestrator.load_module("memory_manager", memory_manager)
    orchestrator.load_module("keyboard_manager", keyboard_manager)
    orchestrator.load_module("web_manager", web_manager)
    
    dev_manager = DevManager()
    web_automation = WebAutomation()
    email_manager = EmailManager()
    business_manager = BusinessManager()
    data_analysis = DataAnalysis()
    orchestrator.load_module("dev_manager", dev_manager)
    orchestrator.load_module("web_automation", web_automation)
    orchestrator.load_module("email_manager", email_manager)
    orchestrator.load_module("business_manager", business_manager)
    orchestrator.load_module("data_analysis", data_analysis)
    
    voice_manager = VoiceManager(recognizer=shared_recognizer, tts=shared_tts)
    threading.Thread(target=voice_manager.preload, daemon=True).start()
    is_busy = False
    teacher_mode_active = False
    teacher_language = ""

    # ============================================================
    # SISTEMA DE PROMPTS PARA O MODO PROFESSORA
    # ============================================================
    TEACHER_PROMPT_TEMPLATE = (
        "Tu es uma professora nativa de {idioma}. O aluno fala portugues.\n"
        "REGRAS DE VOZ: Para o sistema usar a voz correta, deves OBRIGATORIAMENTE iniciar CADA frase com a tag do idioma: [PT] para portugues, ou a tag do idioma alvo (ex: [DE], [EN], [JA], [FR]).\n\n"
        "FORMATO OBRIGATORIO:\n"
        "[PT] Diz o significado da palavra\n"
        "[TAG] Diz a palavra em {idioma}\n"
        "[PT] Como se pronuncia: (escreve a pronuncia)\n"
        "[PT] Exemplo:\n"
        "[TAG] Frase de exemplo em {idioma}\n"
        "[PT] (Tua pergunta para o aluno praticar)\n\n"
        "EXEMPLO de resposta perfeita para Alemao (tag [DE]):\n"
        "[PT] Hoje vamos aprender a dizer obrigado.\n"
        "[DE] Danke\n"
        "[PT] Pronuncia-se: dan-ke. Exemplo:\n"
        "[DE] Danke schoen!\n"
        "[PT] Agora e a tua vez: como se diz obrigado em alemao?\n\n"
        "Nunca mistures idiomas na mesma tag! Mantem as respostas CURTAS."
    )

    def enter_teacher_mode(idioma):
        """Ativa o Modo Professora e entra no loop continuo."""
        nonlocal teacher_mode_active, teacher_language, is_busy
        teacher_mode_active = True
        teacher_language = idioma
        is_busy = True
        
        print(f"\n{'='*50}")
        print(f"[MODO PROFESSORA DE {idioma.upper()} ATIVADO!]")
        print(f"Fale livremente sem tocar em teclas.")
        print(f"Para SAIR: diga 'sair da aula'")
        print(f"{'='*50}\n")
        
        # Limpar historico e injetar personalidade de professora
        orchestrator.conversation_history = []
        orchestrator.teacher_mode = True
        teacher_prompt = TEACHER_PROMPT_TEMPLATE.format(idioma=idioma)
        orchestrator.conversation_history.append({"role": "system", "content": teacher_prompt})
        
        # Saudacao inicial
        overlay.state_changed.emit("thinking")
        saudacao = orchestrator.process_command(f"Comeca a primeira aula. Ensina a primeira palavra basica de {idioma} seguindo o formato.")
        
        overlay.state_changed.emit("speaking")
        voice_manager.speak(saudacao, force_language=teacher_language)
        
        # LOOP CONTÍNUO DE ESCUTA (sem precisar de CTRL)
        while teacher_mode_active:
            # Verificar se o utilizador quer sair (premindo CTRL)
            overlay.state_changed.emit("listening")
            
            text = voice_manager.listen_continuous(duration=4)
            
            if not text:
                continue  # Silêncio, volta a escutar
            
            # Verificar comandos de saída
            text_lower = text.lower()
            exit_keywords = [
                "sair do modo professora", "sair da aula", "sair do modo professor", 
                "sair modo professora", "sair professora", "parar aula", 
                "sair desse modo", "sair deste modo", "quero sair", 
                "terminar aula", "terminar a aula", "parar a aula", "sair modo",
                "não quero aprender", "nao quero aprender", "estou farto",
                "chega", "cala te", "cala-te", "para com isso", "voltar ao normal"
            ]
            if any(cmd in text_lower for cmd in exit_keywords):
                teacher_mode_active = False
                overlay.state_changed.emit("speaking")
                voice_manager.speak("Aula terminada! Foi um prazer ensinar-te. Até à próxima!")
                overlay.state_changed.emit("idle")
                is_busy = False
                # Restaurar o histórico normal
                orchestrator.teacher_mode = False
                orchestrator.conversation_history = []
                print("\n[MODO PROFESSORA DESATIVADO] Voltando ao modo normal.\n")
                return
            
            # Processar a resposta do aluno
            overlay.state_changed.emit("thinking")
            response = orchestrator.process_command(text)
            
            overlay.state_changed.emit("speaking")
            voice_manager.speak(response, force_language=teacher_language)
        
        overlay.state_changed.emit("idle")
        is_busy = False

    def process_cycle():
        """Ciclo normal de comando (Walkie-Talkie com CTRL)."""
        nonlocal is_busy
        is_busy = True
        
        overlay.state_changed.emit("listening")
        text = voice_manager.listen()

        if text is None:
            # Clique acidental no ALT, nem tentou falar: fica em silêncio.
            overlay.state_changed.emit("idle")
            is_busy = False
            return

        if text == "":
            # Tentou falar mas o microfone/reconhecimento falhou: avisar em vez de ficar muda.
            overlay.state_changed.emit("speaking")

            def on_done_erro():
                overlay.state_changed.emit("idle")
                nonlocal is_busy
                is_busy = False

            voice_manager.speak("Não percebi, podes repetir?", callback=on_done_erro)
            return

        # Detetar se o utilizador quer entrar no Modo Professora
        text_lower = text.lower()
        idiomas_map = {
            "inglês": "Inglês", "ingles": "Inglês", "english": "Inglês",
            "japonês": "Japonês", "japones": "Japonês", "japanese": "Japonês",
            "alemão": "Alemão", "alemao": "Alemão", "german": "Alemão",
            "coreano": "Coreano", "korean": "Coreano",
            "espanhol": "Espanhol", "spanish": "Espanhol",
            "francês": "Francês", "frances": "Francês", "french": "Francês",
            "italiano": "Italiano", "italian": "Italiano",
            "mandarim": "Mandarim", "chinês": "Mandarim", "chines": "Mandarim",
        }
        
        # Verificar se é um pedido de Modo Autónomo (tarefas complexas como enviar emails, jogar, tomar o controlo)
        auto_keywords = [
            "assume o controlo", "faz isso por mim", "modo autónomo", "modo autonomo",
            "toma o meu lugar", "toma meu lugar", "envia um email", "envia email", 
            "trata disso", "faz tu", "escreve por mim", "vai jogar", "joga por mim",
            "como um humano", "tarefas por mim"
        ]
        if any(kw in text_lower for kw in auto_keywords):
            print("\n[MODO AUTÓNOMO ATIVADO]")
            overlay.state_changed.emit("thinking")
            response = orchestrator.process_autonomous_goal(text)
            overlay.state_changed.emit("speaking")
            
            def on_done_auto():
                overlay.state_changed.emit("idle")
                nonlocal is_busy
                is_busy = False
                
            voice_manager.speak(response, callback=on_done_auto)
            return

        # Verificar se é um pedido de modo professora / conselheira
        if any(kw in text_lower for kw in ["modo professor", "ensina-me", "ensina me", "aula de", "quero aprender", "modo professora", "pedir conselho", "preciso de um conselho", "quero um conselho", "conselheiro", "conselheira"]):
            idioma_detectado = "Português"  # Default
            for chave, valor in idiomas_map.items():
                if chave in text_lower:
                    idioma_detectado = valor
                    break
            enter_teacher_mode(idioma_detectado)
            return
            
        overlay.state_changed.emit("thinking")
        response = orchestrator.process_command(text)
        
        overlay.state_changed.emit("speaking")
        
        def on_done():
            overlay.state_changed.emit("idle")
            nonlocal is_busy
            is_busy = False
            
        voice_manager.speak(response, callback=on_done)

    def on_hotkey():
        if not is_busy:
            threading.Thread(target=process_cycle, daemon=True).start()

    keyboard.add_hotkey('alt', on_hotkey)

    print("\n" + "="*50)
    print("CORTEX PRONTA (Modo Walkie-Talkie + Professora)")
    print("  ALT = Falar com a Cortex (solte quando terminar)")
    print("  Diga 'modo professora de inglês' para começar uma aula!")
    print("  Na aula, fale livremente sem tocar em teclas.")
    print("  Para sair da aula, diga 'sair do modo professora'.")
    print("="*50 + "\n")
    
    overlay.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    start_cortex()
