import eel
from core.orchestrator import CortexOrchestrator
from modules.file_manager import FileManager
from modules.os_manager import OSManager
from modules.memory_manager import MemoryManager
from modules.vision_manager import VisionManager
from modules.keyboard_manager import KeyboardManager
from modules.web_manager import WebManager
from modules.dev_manager import DevManager
from modules.business_manager import BusinessManager
from modules.data_analysis import DataAnalysis
from modules.email_manager import EmailManager
from modules.web_automation import WebAutomation
from modules.voice_manager import VoiceManager

print("A iniciar o Cérebro da Cortex e Motores de Voz...")
orchestrator = CortexOrchestrator()
orchestrator.load_module("file_manager", FileManager())
orchestrator.load_module("os_manager", OSManager())
orchestrator.load_module("memory_manager", MemoryManager())
orchestrator.load_module("vision_manager", VisionManager())
orchestrator.load_module("keyboard_manager", KeyboardManager())
orchestrator.load_module("web_manager", WebManager())
orchestrator.load_module("dev_manager", DevManager())
orchestrator.load_module("business_manager", BusinessManager())
orchestrator.load_module("data_analysis", DataAnalysis())
orchestrator.load_module("email_manager", EmailManager())
orchestrator.load_module("web_automation", WebAutomation())

voice_manager = VoiceManager()

eel.init('frontend')

@eel.expose
def ui_ready():
    eel.update_status('idle', 'Cortex Pronta.', 'Clique na esfera para falar.')

@eel.expose
def process_voice_input(text):
    """Recebe o texto do JS, processa no Ollama e manda o áudio de volta."""
    if not text:
        return
        
    # Processar no modelo local
    response = orchestrator.process_command(text)
    eel.update_status('speaking', 'A falar...', f'Cortex: "{response}"')
    
    # Gerar o ficheiro MP3
    audio_file = voice_manager.generate_speech_file(response)
    
    # Dizer ao JS para tocar o ficheiro
    if audio_file:
        eel.play_audio(audio_file)
    else:
        on_speech_ended()

@eel.expose
def on_speech_ended():
    """Chamado pelo JS quando o MP3 acaba de tocar."""
    eel.update_status('idle', 'Pronta.', 'Clique na esfera para falar.')

if __name__ == '__main__':
    print("A abrir a interface da Cortex...")
    try:
        # Abre no browser Chrome default, que suporta Web Speech API
        eel.start('index.html', size=(400, 600), port=8000)
    except Exception as e:
        print("Erro ao iniciar a interface gráfica:", e)