import unicodedata
from collections import OrderedDict


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


TOOL_GROUPS = OrderedDict(
    [
        (
            "email",
            {
                "keywords": (
                    "email", "e-mail", "gmail", "correio", "mensagem recebida",
                    "caixa de entrada", "remetente", "destinatario", "anexo",
                    "responder", "resposta para",
                ),
                "tools": (
                    "listar_emails", "ler_email", "criar_rascunho_email",
                    "responder_email", "enviar_email",
                ),
            },
        ),
        (
            "files",
            {
                "keywords": (
                    "ficheiro", "arquivo", "pasta", "diretorio", "documento",
                    "pdf", "docx", "zip", "download", "desktop", "ambiente de trabalho",
                    "backup", "duplicado", "renome", "copi", "move", "apaga",
                ),
                "tools": (
                    "procurar_ficheiros", "ler_ficheiro", "abrir_ficheiro",
                    "ler_pdf_docx", "escrever_ficheiro", "criar_pasta",
                    "mover_ficheiro", "copiar_ficheiro", "renomear_ficheiro",
                    "apagar_ficheiro", "organizar_pasta", "listar_pasta",
                    "descompactar_zip", "criar_backup", "encontrar_duplicados",
                ),
            },
        ),
        (
            "web",
            {
                "keywords": (
                    "internet", "pesquisa", "pesquisar", "procura na web", "google",
                    "site", "pagina", "url", "link", "noticia", "atualizado",
                    "vaga", "emprego",
                ),
                "tools": ("pesquisar_internet", "procurar_empregos"),
            },
        ),
        (
            "vision",
            {
                "keywords": (
                    "ecra", "tela", "monitor", "imagem", "ve o que", "olha para",
                    "screenshot", "captura", "botao", "onde clicar", "o que aparece",
                ),
                "tools": ("analisar_ecra", "tirar_screenshot"),
            },
        ),
        (
            "memory",
            {
                "keywords": (
                    "lembra", "memoriza", "guarda que", "nao te esquecas",
                    "aprende isto", "meu nome", "minha preferencia", "eu gosto",
                    "eu odeio", "eu detesto", "eu prefiro", "prefiro",
                    "costumo", "eu sempre", "eu nunca", "me chamo", "chamo-me",
                    "trabalho como", "a minha rotina", "eu sou", "eu trabalho",
                ),
                "tools": ("guardar_memoria", "aprender"),
            },
        ),
        (
            "tasks",
            {
                "keywords": (
                    "lembrete", "lembra-me", "avisa-me", "agenda", "tarefa",
                    "compromisso", "marca para", "nao te esquecas de me avisar",
                    "lista de tarefas", "lista de lembretes",
                ),
                "tools": (
                    "criar_lembrete", "listar_lembretes",
                    "concluir_lembrete", "cancelar_lembrete",
                ),
            },
        ),
        (
            "keyboard",
            {
                "keywords": (
                    "digita", "escreve no", "teclado", "atalho", "pressiona",
                    "clica", "rato", "mouse", "ctrl+", "alt+", "arrasta",
                    "area de transferencia", "clipboard", "copia isto", "cola isto",
                ),
                "tools": (
                    "digitar_texto", "pressionar_teclas", "segurar_tecla",
                    "mover_rato", "clicar_rato",
                    "ler_area_transferencia", "escrever_area_transferencia",
                ),
            },
        ),
        (
            "windows",
            {
                "keywords": (
                    "janela", "programa", "aplicacao", "aplicativo", "abre o",
                    "abrir o", "fecha o", "minimiza", "maximiza", "spotify",
                    "chrome", "discord", "word", "excel", "vscode", "calculadora",
                    "playlist", "favoritas", "mais ouvidas", "top tracks"
                ),
                "tools": (
                    "open_application", "listar_janelas", "fechar_janela",
                    "minimizar_janela", "maximizar_janela", "alternar_janela",
                    "organizar_janelas", "minimizar_tudo", "play_track", 
                    "pause_playback", "next_track", "current_track",
                    "create_top_tracks_playlist",
                    "listar_programas_instalados",
                ),
            },
        ),
        (
            "system",
            {
                "keywords": (
                    "computador", "sistema", "processo", "cpu", "ram", "gpu",
                    "disco", "volume", "som", "reinicia", "desliga", "bloqueia",
                    "suspende", "terminal", "powershell", "comando", "instala",
                    "temporario", "que horas", "data de hoje",
                ),
                "tools": (
                    "get_current_time", "info_sistema", "listar_processos",
                    "matar_processo", "ajustar_volume", "bloquear_pc",
                    "reiniciar_pc", "shutdown_computer", "suspender_computador",
                    "install_program", "run_terminal_command", "limpar_temporarios",
                ),
            },
        ),
        (
            "development",
            {
                "keywords": (
                    "codigo", "programa", "programar", "python", "javascript",
                    "html", "css", "projeto", "erro no codigo", "desenvolvimento",
                ),
                "tools": (
                    "criar_projeto_python", "criar_projeto_web",
                    "ler_ficheiro", "escrever_ficheiro", "listar_pasta",
                    "run_terminal_command",
                ),
            },
        ),
    ]
)


class ToolRouter:
    """Entrega ao modelo apenas as ferramentas relevantes para o pedido atual."""

    def __init__(self, max_tools: int = 18):
        self.max_tools = max_tools

    def select(self, command: str, schemas: list[dict]) -> list[dict]:
        text = _normalize(command)
        selected_names: list[str] = []

        for group in TOOL_GROUPS.values():
            if any(_normalize(keyword) in text for keyword in group["keywords"]):
                for name in group["tools"]:
                    if name not in selected_names:
                        selected_names.append(name)

        if not selected_names:
            return []

        by_name = {
            schema["function"]["name"]: schema
            for schema in schemas
            if schema.get("function", {}).get("name")
        }
        return [
            by_name[name]
            for name in selected_names[: self.max_tools]
            if name in by_name
        ]
