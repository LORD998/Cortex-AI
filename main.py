import sys
from core.orchestrator import CortexOrchestrator
from modules.file_manager import FileManager
from modules.os_manager import OSManager

def main():
    print("A iniciar o sistema central da Cortex...")
    orchestrator = CortexOrchestrator()
    
    # Carregar os módulos vitais
    orchestrator.load_module("file_manager", FileManager())
    orchestrator.load_module("os_manager", OSManager())
    
    print("\n" + "="*50)
    print("CORTEX - Cérebro Ativo (LLM Tool Calling)")
    print("Escreva 'sair' para terminar.")
    print("="*50 + "\n")
    
    while True:
        try:
            user_input = input("Tu: ")
            if not user_input.strip():
                continue
                
            response = orchestrator.process_command(user_input)
            
            # Limpa o texto "a pensar..." do ecrã
            print("\r" + " "*60 + "\r", end="")
            print(f"Cortex: {response}\n")
            
            if user_input.lower().strip() in ["sair", "exit", "quit"]:
                break
                
        except KeyboardInterrupt:
            print("\nCortex: Interrupção detetada. A encerrar o sistema de forma segura.")
            sys.exit(0)
        except EOFError:
            print("\nCortex: Fim de entrada detetado. A encerrar.")
            break
        except Exception as e:
            print(f"\nCortex: Ocorreu um erro crítico - {str(e)}")

if __name__ == "__main__":
    main()
