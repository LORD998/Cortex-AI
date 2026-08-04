import json
import os
import re
import unicodedata

from core.config import CortexConfig
from core.fast_intents import try_fast_intent
from core.nlp_engine import NLPEngine
from core.tool_router import ToolRouter
from modules.spotify_manager import SpotifyManager

class CortexOrchestrator:
    TOOL_MODULE_REQUIREMENTS = {
        **{name: "dev_manager" for name in ("criar_projeto_python", "criar_projeto_web")},
        **{
            name: "os_manager"
            for name in (
                "listar_janelas", "fechar_janela", "minimizar_janela",
                "suspender_computador", "listar_programas_instalados",
                "alternar_janela", "organizar_janelas", "maximizar_janela",
                "ler_area_transferencia", "escrever_area_transferencia",
                "open_application", "install_program", "get_current_time",
                "listar_processos", "matar_processo", "info_sistema",
                "ajustar_volume", "bloquear_pc", "reiniciar_pc",
                "minimizar_tudo", "tirar_screenshot", "limpar_temporarios",
                "run_terminal_command", "shutdown_computer",
            )
        },
        **{
            name: "file_manager"
            for name in (
                "descompactar_zip", "criar_backup", "encontrar_duplicados",
                "procurar_ficheiros", "ler_ficheiro", "abrir_ficheiro",
                "ler_pdf_docx", "compactar_zip", "escrever_ficheiro",
                "criar_pasta", "mover_ficheiro", "copiar_ficheiro",
                "renomear_ficheiro", "apagar_ficheiro", "organizar_pasta",
                "listar_pasta",
            )
        },
        **{
            name: "email_manager"
            for name in (
                "listar_emails", "ler_email", "criar_rascunho_email",
                "responder_email", "enviar_email",
            )
        },
        **{name: "web_manager" for name in ("pesquisar_internet", "procurar_empregos")},
        **{
            name: "keyboard_manager"
            for name in (
                "digitar_texto", "pressionar_teclas", "segurar_tecla",
                "mover_rato", "clicar_rato",
            )
        },
        **{name: "memory_manager" for name in ("guardar_memoria", "aprender")},
        **{
            name: "task_manager"
            for name in (
                "criar_lembrete", "listar_lembretes",
                "concluir_lembrete", "cancelar_lembrete",
            )
        },
        **{
            name: "spotify_manager"
            for name in (
                "play_track", "pause_playback", "next_track", "current_track",
                "create_top_tracks_playlist",
            )
        },
        "analisar_ecra": "vision_manager",
    }

    RISKY_TOOLS = {
        "apagar_ficheiro",
        "mover_ficheiro",
        "copiar_ficheiro",
        "renomear_ficheiro",
        "escrever_ficheiro",
        "descompactar_zip",
        "organizar_pasta",
        "enviar_email",
        "fechar_janela",
        "install_program",
        "matar_processo",
        "reiniciar_pc",
        "shutdown_computer",
        "suspender_computador",
        "limpar_temporarios",
        "run_terminal_command",
    }

    def __init__(self, nlp=None, config=None):
        self.config = config or CortexConfig.from_env()
        self.modules = {}
        self.name = "Cortex"
        self.nlp = nlp or NLPEngine(config=self.config)
        self.tool_router = ToolRouter(max_tools=self.config.max_tools_per_request)
        self.conversation_history = []
        self.teacher_mode = False
        self.pending_confirmation = None
        
        self.tools_schema = [
            # ============================================================
            # DEV E PROGRAMAÇÃO
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "criar_projeto_python",
                    "description": "Cria um projeto Python completo com ambiente virtual e ficheiros base.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string", "description": "Nome do projeto."},
                            "caminho": {"type": "string", "description": "Onde criar o projeto."}
                        },
                        "required": ["nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "criar_projeto_web",
                    "description": "Cria um projeto Web básico com HTML, CSS e JS.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string", "description": "Nome do projeto."},
                            "caminho": {"type": "string", "description": "Onde criar o projeto."}
                        },
                        "required": ["nome"]
                    }
                }
            },
            # ============================================================
            # GESTÃO DE JANELAS E CLIPBOARD
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "listar_janelas",
                    "description": "Lista todas as janelas abertas no ecrã.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fechar_janela",
                    "description": "Fecha uma janela aberta pelo título (útil para fechar pastas ou programas).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string", "description": "Parte do título da janela ou pasta a fechar."}
                        },
                        "required": ["nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "minimizar_janela",
                    "description": "Minimiza uma janela específica pelo título.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string", "description": "Parte do título da janela."}
                        },
                        "required": ["nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "suspender_computador",
                    "description": "Coloca o computador em suspensão/hibernação.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_programas_instalados",
                    "description": "Lista todas as aplicações instaladas no computador.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "alternar_janela",
                    "description": "Foca numa janela específica (como fazer Alt+Tab).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string", "description": "Parte do nome da janela."}
                        },
                        "required": ["nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "organizar_janelas",
                    "description": "Coloca duas janelas lado-a-lado (Split Screen).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome_esquerda": {"type": "string", "description": "Janela da esquerda."},
                            "nome_direita": {"type": "string", "description": "Janela da direita."}
                        },
                        "required": ["nome_esquerda", "nome_direita"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "maximizar_janela",
                    "description": "Maximiza a janela atual ou uma específica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string", "description": "Nome da janela a maximizar (opcional)."}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ler_area_transferencia",
                    "description": "Lê o texto atual no clipboard (CTRL+C).",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escrever_area_transferencia",
                    "description": "Copia um texto para o clipboard (CTRL+C).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "O texto a copiar."}
                        },
                        "required": ["texto"]
                    }
                }
            },
            # ============================================================
            # FICHEIROS AVANÇADOS
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "descompactar_zip",
                    "description": "Extrai ficheiros de um arquivo ZIP.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ficheiro": {"type": "string", "description": "Caminho do ficheiro ZIP."},
                            "destino": {"type": "string", "description": "Onde extrair (opcional)."}
                        },
                        "required": ["ficheiro"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "criar_backup",
                    "description": "Cria um backup em ZIP de uma pasta.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pasta": {"type": "string", "description": "A pasta a fazer backup."}
                        },
                        "required": ["pasta"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "encontrar_duplicados",
                    "description": "Procura ficheiros duplicados exatos numa pasta e apresenta um relatório sem apagar nada.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pasta": {"type": "string", "description": "A pasta a analisar."}
                        },
                        "required": ["pasta"]
                    }
                }
            },
            # ============================================================
            # APLICAÇÕES E SISTEMA
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Abre uma aplicação/programa no computador (ex: chrome, spotify, discord, word, excel, definições, bloco de notas, calculadora, steam, vscode).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {"type": "string", "description": "O nome do programa a abrir."}
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "install_program",
                    "description": "Instala um novo programa/software no computador do utilizador usando o gestor de pacotes do Windows (winget).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "program_name": {"type": "string", "description": "O nome do programa a instalar (ex: 'VLC', 'OBS Studio', '7zip')."}
                        },
                        "required": ["program_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Obtém a data e hora atual do sistema.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_processos",
                    "description": "Lista os processos em execução no sistema com o consumo de CPU e memória RAM.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "matar_processo",
                    "description": "Encerra/mata um programa que travou ou que queiras fechar à força.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string", "description": "O nome do processo a encerrar (ex: 'chrome', 'spotify', 'discord')."}
                        },
                        "required": ["nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "info_sistema",
                    "description": "Obtém informações detalhadas do computador: CPU, RAM, GPU, espaço em disco.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ajustar_volume",
                    "description": "Ajusta o volume do som do computador.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nivel": {"type": "integer", "description": "O nível de volume de 0 (mudo) a 100 (máximo)."}
                        },
                        "required": ["nivel"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "bloquear_pc",
                    "description": "Bloqueia o ecrã do computador (pede palavra-passe para voltar).",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reiniciar_pc",
                    "description": "Reinicia o computador.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "minimizar_tudo",
                    "description": "Minimiza todas as janelas abertas e mostra o Ambiente de Trabalho.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tirar_screenshot",
                    "description": "Tira uma captura de ecrã e guarda-a no Ambiente de Trabalho.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "caminho": {"type": "string", "description": "Caminho onde guardar (opcional, por defeito: Ambiente de Trabalho)."}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "limpar_temporarios",
                    "description": "Limpa ficheiros temporários do sistema para libertar espaço em disco.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            # ============================================================
            # INTERNET E PESQUISA
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "pesquisar_internet",
                    "description": "Pesquisa no Google/Internet por informação atualizada.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pesquisa": {"type": "string", "description": "Os termos a pesquisar."}
                        },
                        "required": ["pesquisa"]
                    }
                }
            },
            # ============================================================
            # TECLADO E RATO (CONTROLO FÍSICO)
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "digitar_texto",
                    "description": "Digita/escreve texto fisicamente no ecrã usando o teclado virtual. Usa quando o utilizador pedir para escrever algo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "O texto a digitar fisicamente no teclado."}
                        },
                        "required": ["texto"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "pressionar_teclas",
                    "description": "Pressiona atalhos de teclado fisicamente (ex: 'ctrl+w' para fechar aba, 'enter', 'tab', 'win+d' para minimizar tudo).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "teclas": {"type": "string", "description": "O atalho de teclado a pressionar (separado por +, ex: 'ctrl+w')."}
                        },
                        "required": ["teclas"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "segurar_tecla",
                    "description": "Mantém uma tecla pressionada por X segundos. Excelente para jogar jogos (ex: Roblox) para andar com o personagem ('w', 'a', 's', 'd').",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tecla": {"type": "string", "description": "A tecla a segurar (ex: 'w', 'space', 'shift')."},
                            "segundos": {"type": "number", "description": "Quantos segundos manter pressionada."}
                        },
                        "required": ["tecla", "segundos"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mover_rato",
                    "description": "Move o rato fisicamente para as coordenadas exatas do ecrã (X, Y). Útil para navegar interfaces ou apontar num jogo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "Coordenada Horizontal (ex: 0 a 1920)."},
                            "y": {"type": "integer", "description": "Coordenada Vertical (ex: 0 a 1080)."}
                        },
                        "required": ["x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clicar_rato",
                    "description": "Simula um clique do rato (esq/dir) para interagir com o ecrã ou jogar.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "botao": {"type": "string", "description": "O botão do rato: 'left', 'right' ou 'middle'."},
                            "duplo": {"type": "boolean", "description": "Verdadeiro para clique duplo."}
                        },
                        "required": ["botao"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_terminal_command",
                    "description": "Executa um comando no terminal CMD/PowerShell do Windows. Usa para qualquer coisa que precisares fazer no sistema.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "O comando a executar."}
                        },
                        "required": ["command"]
                    }
                }
            },
            # ============================================================
            # MEMÓRIA E APRENDIZAGEM
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "guardar_memoria",
                    "description": "Guarda um facto ou preferência DURADOURA sobre o utilizador para lembrar no futuro. Não uses para coisas triviais, óbvias ou que já constem nas 'Memórias do Utilizador' do teu prompt.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fato": {"type": "string", "description": "O facto a memorizar."}
                        },
                        "required": ["fato"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "aprender",
                    "description": "Armazena conhecimento novo na base de dados interna por tópico (resultados de pesquisas, aulas dadas, etc). Se o tópico já existir, é atualizado automaticamente em vez de duplicado — não precisas de verificar antes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topico": {"type": "string", "description": "O tópico do conhecimento."},
                            "conteudo": {"type": "string", "description": "O conteúdo aprendido."}
                        },
                        "required": ["topico", "conteudo"]
                    }
                }
            },
            # ============================================================
            # LEMBRETES E TAREFAS (AGENDA)
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "criar_lembrete",
                    "description": "Cria um lembrete/tarefa com hora marcada. A Cortex avisa por voz quando chegar a hora. Se o utilizador der um horário relativo (ex: 'daqui a 30 minutos', 'amanhã às 9h'), usa primeiro get_current_time para calcular o valor absoluto de 'quando'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "O que lembrar (ex: 'ligar ao Ricardo')."},
                            "quando": {"type": "string", "description": "Data e hora absolutas no formato 'AAAA-MM-DD HH:MM'."}
                        },
                        "required": ["texto", "quando"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_lembretes",
                    "description": "Lista os lembretes/tarefas pendentes, ordenados por data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "incluir_concluidos": {"type": "boolean", "description": "Se deve incluir lembretes já concluídos (opcional, por defeito falso)."}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "concluir_lembrete",
                    "description": "Marca um lembrete/tarefa como concluído, pelo número (#) ou por parte do texto.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "referencia": {"type": "string", "description": "O número do lembrete ou parte do seu texto."}
                        },
                        "required": ["referencia"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancelar_lembrete",
                    "description": "Apaga um lembrete/tarefa, pelo número (#) ou por parte do texto.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "referencia": {"type": "string", "description": "O número do lembrete ou parte do seu texto."}
                        },
                        "required": ["referencia"]
                    }
                }
            },
            # ============================================================
            # VISÃO (ANÁLISE DO ECRÃ)
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "analisar_ecra",
                    "description": "Tira uma foto ao ecrã para 'ver' o que está no PC do utilizador.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pergunta": {"type": "string", "description": "O que procurar na imagem."}
                        },
                        "required": ["pergunta"]
                    }
                }
            },
            # ============================================================
            # SPOTIFY
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "play_track",
                    "description": "Abre o Spotify e toca uma música específica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "track_name": {"type": "string", "description": "O nome da música."}
                        },
                        "required": ["track_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "pause_playback",
                    "description": "Pausa a música atual no Spotify.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "next_track",
                    "description": "Passa para a próxima música no Spotify.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "current_track",
                    "description": "Vê qual é a música a tocar no Spotify agora.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_top_tracks_playlist",
                    "description": "Cria uma playlist no Spotify com as músicas mais ouvidas do utilizador.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            # ============================================================
            # GESTÃO DE FICHEIROS
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "procurar_ficheiros",
                    "description": "Procura ficheiros no computador por nome.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string", "description": "Nome ou parte do nome do ficheiro."},
                            "diretorio_base": {"type": "string", "description": "Pasta inicial (opcional, por defeito: Desktop)."}
                        },
                        "required": ["nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ler_ficheiro",
                    "description": "Lê o conteúdo de um ficheiro de texto, código, JSON, CSV, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "caminho": {"type": "string", "description": "Caminho absoluto do ficheiro."}
                        },
                        "required": ["caminho"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escrever_ficheiro",
                    "description": "Cria ou modifica um ficheiro de texto no disco.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "caminho": {"type": "string", "description": "Caminho do ficheiro."},
                            "conteudo": {"type": "string", "description": "Conteúdo a escrever."}
                        },
                        "required": ["caminho", "conteudo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "criar_pasta",
                    "description": "Cria uma nova pasta no disco.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "caminho": {"type": "string", "description": "Caminho da pasta a criar."}
                        },
                        "required": ["caminho"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mover_ficheiro",
                    "description": "Move um ficheiro ou pasta de um local para outro.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origem": {"type": "string", "description": "Caminho de origem."},
                            "destino": {"type": "string", "description": "Caminho de destino."}
                        },
                        "required": ["origem", "destino"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "copiar_ficheiro",
                    "description": "Copia um ficheiro ou pasta para outro local.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origem": {"type": "string", "description": "Caminho de origem."},
                            "destino": {"type": "string", "description": "Caminho de destino."}
                        },
                        "required": ["origem", "destino"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "renomear_ficheiro",
                    "description": "Renomeia um ficheiro ou pasta.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "caminho": {"type": "string", "description": "Caminho do ficheiro ou pasta."},
                            "novo_nome": {"type": "string", "description": "O novo nome."}
                        },
                        "required": ["caminho", "novo_nome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apagar_ficheiro",
                    "description": "Apaga um ficheiro ou pasta do disco.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "caminho": {"type": "string", "description": "Caminho do ficheiro ou pasta a apagar."}
                        },
                        "required": ["caminho"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "organizar_pasta",
                    "description": "Organiza automaticamente os ficheiros de uma pasta por tipo (separa imagens, vídeos, documentos, código, música, etc. em sub-pastas).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "caminho": {"type": "string", "description": "Caminho da pasta a organizar."}
                        },
                        "required": ["caminho"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "listar_pasta",
                    "description": "Lista o conteúdo detalhado de uma pasta com tamanhos de ficheiros.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "caminho": {"type": "string", "description": "Caminho da pasta a listar."}
                        },
                        "required": ["caminho"]
                    }
                }
            },
            # ============================================================
            # COMPUTADOR (DESLIGAR)
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "shutdown_computer",
                    "description": "Desliga o computador.",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            # ============================================================
            # EMAIL E CARREIRA
            # ============================================================
            {
                "type": "function",
                "function": {
                    "name": "listar_emails",
                    "description": "Lista os e-mails mais recentes recebidos no Gmail do utilizador.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "quantidade": {"type": "integer", "description": "Número de e-mails a listar (opcional, defeito 5)."}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ler_email",
                    "description": "Lê o conteúdo de um e-mail específico pelo seu ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "O ID do e-mail a ler."}
                        },
                        "required": ["id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "criar_rascunho_email",
                    "description": "Cria um rascunho no Gmail sem o enviar. É a opção preferida para preparar e-mails.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destinatario": {"type": "string", "description": "O endereço de e-mail de destino."},
                            "assunto": {"type": "string", "description": "O assunto do e-mail."},
                            "corpo": {"type": "string", "description": "O conteúdo/corpo do e-mail."},
                            "anexo_caminho": {"type": "string", "description": "Caminho absoluto opcional de um anexo."}
                        },
                        "required": ["destinatario", "assunto", "corpo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "responder_email",
                    "description": "Prepara no Gmail um rascunho de resposta a um e-mail existente; não envia.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "O ID do e-mail original."},
                            "corpo": {"type": "string", "description": "O texto da resposta."}
                        },
                        "required": ["id", "corpo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enviar_email",
                    "description": "Envia um e-mail. Esta ação exige confirmação explícita do utilizador.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destinatario": {"type": "string", "description": "O endereço de e-mail de destino."},
                            "assunto": {"type": "string", "description": "O assunto do e-mail."},
                            "corpo": {"type": "string", "description": "O conteúdo/corpo do e-mail a enviar."},
                            "anexo_caminho": {"type": "string", "description": "Opcional. Caminho absoluto do ficheiro a enviar como anexo."}
                        },
                        "required": ["destinatario", "assunto", "corpo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "procurar_empregos",
                    "description": "Pesquisa e resume vagas de emprego e oportunidades profissionais.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cargo": {"type": "string", "description": "O cargo ou profissão a pesquisar (ex: 'Programador Python', 'Designer')."},
                            "localizacao": {"type": "string", "description": "A localização (ex: 'Portugal', 'Lisboa', 'Remoto')."}
                        },
                        "required": ["cargo"]
                    }
                }
            }
        ]

    def load_module(self, name, module_instance):
        self.modules[name] = module_instance
        print(f"[{self.name}] Módulo '{name}' carregado e ligado ao Cérebro.")

    def _system_prompt(self, memories: str) -> str:
        if self.teacher_mode:
            return (
                "És a Cortex em modo tutora de idiomas. Ensina de forma prática e "
                "adaptativa: explica pouco, dá um exemplo, pede uma resposta ao aluno "
                "e corrige com delicadeza. Responde no idioma que o utilizador está a "
                "aprender, acompanhado de Português quando isso ajudar. Mantém o nível "
                "e o progresso usando o histórico. Nunca inventes que executaste uma ação."
                f"\nMemória relevante: {memories or 'sem memórias relevantes'}"
            )

        confirmation_rule = (
            "- Para e-mail, prefere criar um rascunho; o envio exige confirmação do utilizador.\n"
            "- Ações destrutivas, instalações, comandos de terminal e alterações sensíveis exigem confirmação.\n"
            if self.config.confirm_risky_actions
            else "- Executa diretamente a ação pedida, incluindo as sensíveis (apagar, enviar, "
            "desligar, terminal); não perguntes por confirmação em texto, o sistema já não a exige.\n"
        )
        return (
            "És a Cortex, assistente pessoal local no Windows. Compreende Português "
            "informal, erros ortográficos, frases incompletas e mudanças de idioma. "
            "Responde em Português do Brasil natural, de forma clara e curta, mas "
            "usa mais detalhe quando for útil. Evita construções de Português europeu.\n"
            "REGRAS:\n"
            "- Tens acesso amplo às ferramentas carregadas; escolhe e combina as necessárias para concluir o objetivo.\n"
            "- Descobre o objetivo real e usa ferramentas quando uma ação ou dado real for necessário.\n"
            "- Nunca afirmes que fizeste algo sem um resultado de ferramenta que confirme isso.\n"
            "- Se uma ferramenta falhar, explica exatamente o que falhou e propõe a alternativa segura.\n"
            "- Não inventes fontes, e-mails, ficheiros, janelas ou resultados.\n"
            "- Não uses Markdown complexo porque a resposta pode ser lida em voz alta.\n"
            "- Modo aprendizado sempre ativo: sempre que o utilizador revelar uma preferência, "
            "hábito, rotina, facto pessoal, correção a algo que disseste, ou ensinar-te algo novo "
            "— mesmo sem pedir explicitamente para memorizar — chama guardar_memoria (factos/"
            "preferências curtas) ou aprender (conhecimento/tópicos mais longos) na mesma resposta, "
            "sem interromper nem perguntar permissão para isso.\n"
            f"{confirmation_rule}"
            "- Se o pedido for apenas conversa, explicação, tradução ou aprendizagem, responde diretamente.\n"
            f"Memória relevante: {memories or 'sem memórias relevantes'}"
        )

    def _should_reason(self, command: str, selected_tools: list[dict]) -> bool:
        """Ativa raciocínio profundo apenas quando o pedido realmente beneficia dele."""
        mode = self.config.reasoning_mode
        if mode in {"on", "true", "1", "always", "sempre"}:
            return True
        if mode in {"off", "false", "0", "never", "nunca"}:
            return False

        normalized = unicodedata.normalize("NFKD", command.casefold())
        normalized = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        complex_signals = (
            r"\banalis",
            r"\bplane",
            r"\bcompara",
            r"\bdiagnostic",
            r"\binvestig",
            r"\bpesquisa.+(?:depois|e depois|em seguida)",
            r"\bresolve",
            r"\bexplica.+(?:porque|por que|como funciona)",
            r"\borganiza tudo\b",
            r"\bvarios passos\b",
            r"\bpasso a passo\b",
            r"\bdecide\b",
            r"\bmelhor estrategia\b",
            r"\bcria (?:um )?(?:plano|projeto|projecto)\b",
        )
        # O modo "think" no qwen3:8b, neste hardware, gera a ~9 tokens/s (menos de
        # metade da velocidade normal) — um pedido pode facilmente demorar 1-3
        # minutos. Por isso só ativa com um sinal explícito de tarefa complexa,
        # nunca por comprimento de frase (fácil de disparar sem querer ao ditar).
        return any(re.search(pattern, normalized) for pattern in complex_signals)

    @staticmethod
    def _is_confirmation(command: str) -> bool:
        normalized = command.casefold().strip()
        return normalized in {
            "sim", "confirmo", "confirmar", "pode", "podes", "pode fazer",
            "podes fazer", "faz", "executa", "envia", "yes", "ok",
        }

    @staticmethod
    def _is_cancellation(command: str) -> bool:
        normalized = command.casefold().strip()
        return normalized in {
            "não", "nao", "cancela", "cancelar", "para", "parar", "esquece",
            "não faças", "nao facas", "no",
        }

    @staticmethod
    def _describe_action(name: str, args: dict) -> str:
        if name == "enviar_email":
            return (
                f"enviar o e-mail para {args.get('destinatario', '?')} "
                f"com o assunto “{args.get('assunto', 'sem assunto')}”"
            )
        if name in {"apagar_ficheiro", "mover_ficheiro", "renomear_ficheiro"}:
            target = args.get("caminho") or args.get("origem") or "o ficheiro indicado"
            return f"{name.replace('_', ' ')}: {target}"
        if name == "run_terminal_command":
            return f"executar no terminal: {args.get('command', '')[:160]}"
        if name == "install_program":
            return f"instalar {args.get('program_name', 'o programa indicado')}"
        return name.replace("_", " ")

    def _confirmation_prompt(self, tool_calls: list[dict]) -> str:
        descriptions = [
            self._describe_action(
                call.get("function", {}).get("name", "ação"),
                call.get("function", {}).get("arguments", {}) or {},
            )
            for call in tool_calls
        ]
        return (
            "Preciso da tua confirmação antes de "
            + "; ".join(descriptions)
            + ". Diz “confirmo” para executar ou “cancela” para parar."
        )

    def _handle_pending_confirmation(self, command: str):
        if not self.pending_confirmation:
            return None
        if self._is_cancellation(command):
            self.pending_confirmation = None
            result = "Ação cancelada. Não alterei nada."
            self.conversation_history.extend(
                [
                    {"role": "user", "content": command},
                    {"role": "assistant", "content": result},
                ]
            )
            return result
        if not self._is_confirmation(command):
            return (
                "Ainda tenho uma ação sensível pendente. Diz “confirmo” para executar "
                "ou “cancela” para a abandonar."
            )

        pending = self.pending_confirmation
        self.pending_confirmation = None
        results = []
        for tool_call in pending:
            function = tool_call.get("function", {})
            name = function.get("name", "")
            args = function.get("arguments", {}) or {}
            print(f"[{self.name} a executar ação confirmada: {name}...]", end="\r")
            results.append(str(self._execute_tool(name, args)))

        response = " ".join(results) if results else "Não havia nenhuma ação para executar."
        self.conversation_history.extend(
            [
                {"role": "user", "content": command},
                {"role": "assistant", "content": response},
            ]
        )
        return response

    def _trim_history(self):
        limit = self.config.max_history_messages
        if len(self.conversation_history) > limit + 1:
            self.conversation_history = [
                self.conversation_history[0],
                *self.conversation_history[-limit:],
            ]

    def _available_tool_schemas(self):
        available = []
        for schema in self.tools_schema:
            name = schema.get("function", {}).get("name")
            required_module = self.TOOL_MODULE_REQUIREMENTS.get(name)
            if required_module is None or required_module in self.modules:
                available.append(schema)
        return available

    def process_command_stream(self, command: str):
        command = command.strip()
        if not command:
            yield "Não ouvi nenhum pedido."
            return

        pending_response = self._handle_pending_confirmation(command)
        if pending_response is not None:
            yield pending_response
            return

        if command.casefold() in {"sair", "exit", "quit"}:
            yield "Até logo! A encerrar de forma segura."
            return

        fast_result = try_fast_intent(command, self.modules)
        if fast_result is not None:
            self.conversation_history.extend(
                [
                    {"role": "user", "content": command},
                    {"role": "assistant", "content": fast_result},
                ]
            )
            self._trim_history()
            yield fast_result
            return

        memories = ""
        if "memory_manager" in self.modules:
            memories = self.modules["memory_manager"].relembrar()

        system_prompt = self._system_prompt(memories)
        if self.conversation_history and self.conversation_history[0].get("role") == "system":
            self.conversation_history[0] = {"role": "system", "content": system_prompt}
        else:
            self.conversation_history.insert(0, {"role": "system", "content": system_prompt})

        previous_user_text = " ".join(
            message.get("content", "")
            for message in self.conversation_history[-4:]
            if message.get("role") == "user"
        )
        self.conversation_history.append({"role": "user", "content": command})
        self._trim_history()

        routing_text = f"{previous_user_text} {command}".strip()
        selected_tools = self.tool_router.select(
            routing_text,
            self._available_tool_schemas(),
        )
        use_reasoning = self._should_reason(command, selected_tools)

        # Se houver ferramentas, o Worker trabalha no fundo enquanto a partição principal diz OK.
        if selected_tools:
            yield "A tratar do teu pedido..."

        for step in range(1, self.config.max_agent_steps + 1):
            mode_label = "raciocínio" if use_reasoning else "rápido"
            print(f"[{self.name} a pensar: passo {step}, modo {mode_label}...]", end="\r")
            
            tool_calls = []
            full_content = ""
            
            for chunk in self.nlp.process_stream_with_tools(
                self.conversation_history,
                tools=selected_tools or None,
                think=use_reasoning,
            ):
                if chunk["type"] == "content":
                    full_content += chunk["content"]
                    # Streaming em tempo real palavra a palavra (apenas se não houver ferramentas)
                    if not selected_tools:
                        yield chunk["content"]
                elif chunk["type"] == "tool_calls":
                    tool_calls = chunk["calls"]

            message = {"role": "assistant"}
            if full_content:
                message["content"] = full_content
            if tool_calls:
                message["tool_calls"] = tool_calls

            if not tool_calls:
                self.conversation_history.append(message)
                self._trim_history()
                if selected_tools and full_content:
                    # Se tínhamos ferramentas mas ele decidiu falar, enviamos agora.
                    yield full_content
                if not full_content:
                    yield "Não consegui responder."
                return

            if self.config.confirm_risky_actions and any(
                call.get("function", {}).get("name") in self.RISKY_TOOLS
                for call in tool_calls
            ):
                self.pending_confirmation = tool_calls
                prompt = self._confirmation_prompt(tool_calls)
                self.conversation_history.append({"role": "assistant", "content": prompt})
                self._trim_history()
                yield prompt
                return

            self.conversation_history.append(message)
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                function_name = function.get("name", "")
                arguments = function.get("arguments", {}) or {}
                print(f"[{self.name} a executar: {function_name}...]", end="\r")
                
                try:
                    raw_result = self._execute_tool(function_name, arguments)
                except Exception as exc:
                    raw_result = f"Erro interno ao executar {function_name}: {exc}"

                result_text = str(raw_result)
                envelope = {
                    "ok": not result_text.casefold().startswith(("erro", "falha")),
                    "tool": function_name,
                    "result": result_text[:8000],
                }
                self.conversation_history.append(
                    {
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(envelope, ensure_ascii=False),
                    }
                )

        response = (
            "A tarefa atingiu o limite de passos antes de ficar concluída. "
            "Parei para não executar ações indefinidamente."
        )
        self.conversation_history.append({"role": "assistant", "content": response})
        self._trim_history()
        return response

    def process_autonomous_goal(self, goal: str) -> str:
        """Compatibilidade com a UI antiga; o ciclo normal já é multi-etapas."""
        return self.process_command(goal)

    def _execute_tool(self, name, args):
        # DEV MANAGER
        if name == "criar_projeto_python" and "dev_manager" in self.modules:
            default_path = os.path.join(os.path.expanduser("~"), "Desktop")
            return self.modules["dev_manager"].criar_projeto_python(args.get("nome", ""), args.get("caminho", default_path))
        elif name == "criar_projeto_web" and "dev_manager" in self.modules:
            default_path = os.path.join(os.path.expanduser("~"), "Desktop")
            return self.modules["dev_manager"].criar_projeto_web(args.get("nome", ""), args.get("caminho", default_path))
        
        # JANELAS E CLIPBOARD (os_manager)
        elif name == "listar_janelas" and "os_manager" in self.modules:
            return self.modules["os_manager"].listar_janelas()
        elif name == "fechar_janela" and "os_manager" in self.modules:
            return self.modules["os_manager"].fechar_janela(args.get("nome", ""))
        elif name == "minimizar_janela" and "os_manager" in self.modules:
            return self.modules["os_manager"].minimizar_janela(args.get("nome", ""))
        elif name == "suspender_computador" and "os_manager" in self.modules:
            return self.modules["os_manager"].suspender_computador()
        elif name == "listar_programas_instalados" and "os_manager" in self.modules:
            return self.modules["os_manager"].listar_programas_instalados()
        elif name == "alternar_janela" and "os_manager" in self.modules:
            return self.modules["os_manager"].alternar_janela(args.get("nome", ""))
        elif name == "organizar_janelas" and "os_manager" in self.modules:
            return self.modules["os_manager"].organizar_janelas(args.get("nome_esquerda", ""), args.get("nome_direita", ""))
        elif name == "maximizar_janela" and "os_manager" in self.modules:
            return self.modules["os_manager"].maximizar_janela(args.get("nome", ""))
        elif name == "ler_area_transferencia" and "os_manager" in self.modules:
            return self.modules["os_manager"].ler_area_transferencia()
        elif name == "escrever_area_transferencia" and "os_manager" in self.modules:
            return self.modules["os_manager"].escrever_area_transferencia(args.get("texto", ""))
            
        # FICHEIROS AVANÇADOS (file_manager)
        elif name == "descompactar_zip" and "file_manager" in self.modules:
            return self.modules["file_manager"].descompactar_zip(args.get("ficheiro", ""), args.get("destino", ""))
        elif name == "criar_backup" and "file_manager" in self.modules:
            return self.modules["file_manager"].criar_backup(args.get("pasta", ""))
        elif name == "encontrar_duplicados" and "file_manager" in self.modules:
            return self.modules["file_manager"].encontrar_duplicados(args.get("pasta", ""))

        # EMAIL E CARREIRA
        elif name == "listar_emails" and "email_manager" in self.modules:
            return self.modules["email_manager"].listar_mensagens(args.get("quantidade", 5))
        elif name == "ler_email" and "email_manager" in self.modules:
            return self.modules["email_manager"].ler_mensagem(args.get("id", ""))
        elif name == "criar_rascunho_email" and "email_manager" in self.modules:
            return self.modules["email_manager"].criar_rascunho(
                args.get("destinatario", ""),
                args.get("assunto", ""),
                args.get("corpo", ""),
                args.get("anexo_caminho"),
            )
        elif name == "responder_email" and "email_manager" in self.modules:
            return self.modules["email_manager"].criar_rascunho_resposta(
                args.get("id", ""),
                args.get("corpo", ""),
            )
        elif name == "enviar_email" and "email_manager" in self.modules:
            return self.modules["email_manager"].enviar_email(args.get("destinatario", ""), args.get("assunto", ""), args.get("corpo", ""), args.get("anexo_caminho", None))
        elif name == "procurar_empregos" and "web_manager" in self.modules:
            return self.modules["web_manager"].procurar_empregos(args.get("cargo", ""), args.get("localizacao", "Portugal"))

        """Ponte física entre a IA e o computador."""
        # APLICAÇÕES
        if name == "open_application" and "os_manager" in self.modules:
            result = self.modules["os_manager"].open_application(args.get("app_name", ""))
            if "memory_manager" in self.modules:
                self.modules["memory_manager"].registar_uso_app(args.get("app_name", ""))
            return result
        elif name == "install_program" and "os_manager" in self.modules:
            return self.modules["os_manager"].install_program(args.get("program_name", ""))
        elif name == "get_current_time" and "os_manager" in self.modules:
            return self.modules["os_manager"].get_current_time()
        # SISTEMA
        elif name == "listar_processos" and "os_manager" in self.modules:
            return self.modules["os_manager"].listar_processos()
        elif name == "matar_processo" and "os_manager" in self.modules:
            return self.modules["os_manager"].matar_processo(args.get("nome", ""))
        elif name == "info_sistema" and "os_manager" in self.modules:
            return self.modules["os_manager"].info_sistema()
        elif name == "ajustar_volume" and "os_manager" in self.modules:
            return self.modules["os_manager"].ajustar_volume(int(args.get("nivel", 50)))
        elif name == "bloquear_pc" and "os_manager" in self.modules:
            return self.modules["os_manager"].bloquear_pc()
        elif name == "reiniciar_pc" and "os_manager" in self.modules:
            return self.modules["os_manager"].reiniciar_pc()
        elif name == "minimizar_tudo" and "os_manager" in self.modules:
            return self.modules["os_manager"].minimizar_tudo()
        elif name == "tirar_screenshot" and "os_manager" in self.modules:
            return self.modules["os_manager"].tirar_screenshot(args.get("caminho"))
        elif name == "limpar_temporarios" and "os_manager" in self.modules:
            return self.modules["os_manager"].limpar_temporarios()
        # INTERNET
        elif name == "pesquisar_internet" and "web_manager" in self.modules:
            return self.modules["web_manager"].pesquisar_internet(args.get("pesquisa", ""))
        # TECLADO E RATO
        elif name == "digitar_texto" and "keyboard_manager" in self.modules:
            return self.modules["keyboard_manager"].digitar_texto(args.get("texto", ""))
        elif name == "pressionar_teclas" and "keyboard_manager" in self.modules:
            return self.modules["keyboard_manager"].press_hotkey(args.get("teclas", ""))
        elif name == "segurar_tecla" and "keyboard_manager" in self.modules:
            return self.modules["keyboard_manager"].segurar_tecla(args.get("tecla", ""), float(args.get("segundos", 1.0)))
        elif name == "clicar_rato" and "keyboard_manager" in self.modules:
            return self.modules["keyboard_manager"].clicar_rato(args.get("botao", "left"), bool(args.get("duplo", False)))
        elif name == "mover_rato" and "keyboard_manager" in self.modules:
            return self.modules["keyboard_manager"].mover_rato(int(args.get("x", 0)), int(args.get("y", 0)))
        elif name == "run_terminal_command" and "os_manager" in self.modules:
            return self.modules["os_manager"].run_terminal_command(args.get("command", ""))
        # MEMÓRIA
        elif name == "guardar_memoria" and "memory_manager" in self.modules:
            return self.modules["memory_manager"].guardar_memoria(args.get("fato", ""))
        elif name == "aprender" and "memory_manager" in self.modules:
            return self.modules["memory_manager"].aprender(args.get("topico", ""), args.get("conteudo", ""))
        # LEMBRETES E TAREFAS
        elif name == "criar_lembrete" and "task_manager" in self.modules:
            return self.modules["task_manager"].criar_lembrete(args.get("texto", ""), args.get("quando", ""))
        elif name == "listar_lembretes" and "task_manager" in self.modules:
            return self.modules["task_manager"].listar_lembretes(bool(args.get("incluir_concluidos", False)))
        elif name == "concluir_lembrete" and "task_manager" in self.modules:
            return self.modules["task_manager"].concluir_lembrete(args.get("referencia", ""))
        elif name == "cancelar_lembrete" and "task_manager" in self.modules:
            return self.modules["task_manager"].cancelar_lembrete(args.get("referencia", ""))
        # VISÃO
        elif name == "analisar_ecra" and "vision_manager" in self.modules:
            return self.modules["vision_manager"].analisar_ecra(args.get("pergunta", "Descreve o que vês."))
        # SPOTIFY
        elif name == "play_track" and "spotify_manager" in self.modules:
            return self.modules["spotify_manager"].play_track(args.get("track_name", ""))
        elif name == "pause_playback" and "spotify_manager" in self.modules:
            return self.modules["spotify_manager"].pause_playback()
        elif name == "next_track" and "spotify_manager" in self.modules:
            return self.modules["spotify_manager"].next_track()
        elif name == "current_track" and "spotify_manager" in self.modules:
            return self.modules["spotify_manager"].current_track()
        elif name == "create_top_tracks_playlist" and "spotify_manager" in self.modules:
            return self.modules["spotify_manager"].create_top_tracks_playlist()
        # FICHEIROS
        elif name == "procurar_ficheiros" and "file_manager" in self.modules:
            return self.modules["file_manager"].procurar_ficheiros(args.get("nome", ""), args.get("diretorio_base"))
        elif name == "ler_ficheiro" and "file_manager" in self.modules:
            return self.modules["file_manager"].ler_ficheiro(args.get("caminho", ""))
        elif name == "abrir_ficheiro" and "file_manager" in self.modules:
            return self.modules["file_manager"].abrir_ficheiro(args.get("caminho", ""))
        elif name == "ler_pdf_docx" and "file_manager" in self.modules:
            return self.modules["file_manager"].ler_pdf_docx(args.get("caminho", ""))
        elif name == "compactar_zip" and "file_manager" in self.modules:
            return self.modules["file_manager"].compactar_zip(args.get("caminho", ""), args.get("destino_zip", ""))
        elif name == "escrever_ficheiro" and "file_manager" in self.modules:
            return self.modules["file_manager"].escrever_ficheiro(args.get("caminho", ""), args.get("conteudo", ""))
        elif name == "criar_pasta" and "file_manager" in self.modules:
            return self.modules["file_manager"].criar_pasta(args.get("caminho", ""))
        elif name == "mover_ficheiro" and "file_manager" in self.modules:
            return self.modules["file_manager"].mover_ficheiro(args.get("origem", ""), args.get("destino", ""))
        elif name == "copiar_ficheiro" and "file_manager" in self.modules:
            return self.modules["file_manager"].copiar_ficheiro(args.get("origem", ""), args.get("destino", ""))
        elif name == "renomear_ficheiro" and "file_manager" in self.modules:
            return self.modules["file_manager"].renomear_ficheiro(args.get("caminho", ""), args.get("novo_nome", ""))
        elif name == "apagar_ficheiro" and "file_manager" in self.modules:
            return self.modules["file_manager"].apagar_ficheiro(args.get("caminho", ""))
        elif name == "organizar_pasta" and "file_manager" in self.modules:
            return self.modules["file_manager"].organizar_pasta(args.get("caminho", ""))
        elif name == "listar_pasta" and "file_manager" in self.modules:
            return self.modules["file_manager"].listar_pasta(args.get("caminho", ""))
        # COMPUTADOR
        elif name == "shutdown_computer" and "os_manager" in self.modules:
            return self.modules["os_manager"].shutdown_computer()
        else:
            return f"Ferramenta '{name}' não encontrada nos módulos carregados."

    def process_command(self, command: str) -> str:
        """Versão bloqueante que agrega o iterador (mantém compatibilidade)."""
        return "".join(self.process_command_stream(command))
