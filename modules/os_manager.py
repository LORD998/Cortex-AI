import os
import subprocess
import datetime
import ctypes
import shutil

class OSManager:
    def __init__(self):
        # Base de dados massiva de atalhos de aplicações conhecidas
        self.app_aliases = {
            # Browsers
            "chrome": "chrome", "google chrome": "chrome", "google": "chrome",
            "firefox": "firefox", "brave": "brave", "edge": "msedge", "opera": "opera",
            # Sistema
            "notepad": "notepad", "bloco de notas": "notepad", "notas": "notepad",
            "calculadora": "calc", "calc": "calc",
            "explorer": "explorer", "pastas": "explorer", "ficheiros": "explorer",
            "cmd": "cmd", "terminal": "cmd", "prompt": "cmd",
            "powershell": "powershell",
            "paint": "mspaint", "mspaint": "mspaint",
            "task manager": "taskmgr", "gestor de tarefas": "taskmgr", "taskmgr": "taskmgr",
            # Office
            "word": "winword", "excel": "excel", "powerpoint": "powerpnt",
            "outlook": "outlook",
            # Media
            "spotify": "spotify", "discord": "discord",
            "vlc": "vlc", "media player": "wmplayer",
            "whatsapp": "whatsapp:",
            # Dev & Jogos
            "vscode": "code", "visual studio code": "code", "code": "code",
            "steam": "steam", "roblox": "roblox-player:",
            # Definições
            "definições": "ms-settings:", "settings": "ms-settings:", "definicoes": "ms-settings:",
            "wifi": "ms-settings:network-wifi", "bluetooth": "ms-settings:bluetooth",
            "som": "ms-settings:sound", "display": "ms-settings:display",
        }

    def get_current_time(self):
        """Retorna a data e hora atual do sistema."""
        now = datetime.datetime.now()
        dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        dia_semana = dias[now.weekday()]
        mes = meses[now.month - 1]
        return f"Hoje é {dia_semana}, {now.day} de {mes} de {now.year}. São {now.strftime('%H:%M:%S')}."

    def open_application(self, app_name: str):
        """Abre QUALQUER aplicação no Windows usando múltiplas estratégias."""
        app_lower = app_name.lower().strip()
        
        # 1. Verificar na base de dados de aliases
        target = self.app_aliases.get(app_lower)
        if target:
            try:
                if target.startswith("ms-settings") or target.endswith(":"):
                    os.system(f"start {target}")
                else:
                    subprocess.Popen(f"start {target}", shell=True)
                return f"Sucesso! A aplicação '{app_name}' foi lançada via alias."
            except:
                pass
                
        # 2. Pesquisar agressivamente nos atalhos do Windows (Menu Iniciar)
        import glob
        import os
        
        start_menu_paths = [
            os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), r"Microsoft\Windows\Start Menu\Programs\**\*.lnk"),
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\**\*.lnk"),
            os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), r"Desktop\*.lnk"),
            os.path.join(os.path.expanduser("~"), r"Desktop\*.lnk")
        ]
        
        # Procurar um atalho que contenha o nome do programa
        for base_path in start_menu_paths:
            for lnk in glob.glob(base_path, recursive=True):
                if app_lower in os.path.basename(lnk).lower():
                    try:
                        os.startfile(lnk)
                        return f"Sucesso! Encontrei e lancei o atalho '{os.path.basename(lnk)}'."
                    except Exception as e:
                        pass
        
        # 3. Fallback: tentar abrir diretamente (caso esteja no PATH, como 'calc', 'notepad')
        try:
            subprocess.Popen(f"start {app_lower}", shell=True)
            return f"A tentar lançar '{app_name}' usando os comandos do sistema."
        except Exception as e:
            return f"Não consegui encontrar nem abrir a aplicação '{app_name}'."

    def install_program(self, program_name: str):
        """Instala um programa usando o winget (gestor de pacotes nativo do Windows)."""
        try:
            result = subprocess.run(
                f"winget install --accept-source-agreements --accept-package-agreements {program_name}",
                shell=True, capture_output=True, text=True, timeout=120
            )
            output = result.stdout.strip() + "\n" + result.stderr.strip()
            if result.returncode == 0:
                return f"Sucesso! O programa '{program_name}' foi instalado com sucesso.\n{output[:500]}"
            else:
                return f"Erro ao instalar '{program_name}'.\n{output[:500]}"
        except subprocess.TimeoutExpired:
            return f"A instalação de '{program_name}' está a demorar. Foi iniciada em segundo plano."
        except Exception as e:
            return f"Erro fatal ao instalar: {str(e)}"

    def shutdown_computer(self):
        """Desliga o computador."""
        try:
            os.system("shutdown /s /t 5")
            return "A desligar o computador em 5 segundos."
        except Exception as e:
            return f"Erro ao tentar desligar: {str(e)}"
            
    def reiniciar_pc(self):
        """Reinicia o computador."""
        try:
            os.system("shutdown /r /t 5")
            return "A reiniciar o computador em 5 segundos."
        except Exception as e:
            return f"Erro ao reiniciar: {str(e)}"

    def bloquear_pc(self):
        """Bloqueia o ecrã do computador."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Ecrã bloqueado com sucesso."
        except Exception as e:
            return f"Erro ao bloquear: {str(e)}"

    def run_terminal_command(self, command: str):
        """Executa comandos no terminal do Windows para controlo total do sistema."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode == 0:
                return f"Comando executado com sucesso.\nSaída:\n{output}"[:2000]
            else:
                return f"Erro a executar comando.\nCódigo: {result.returncode}\nErro:\n{error}"[:2000]
        except subprocess.TimeoutExpired:
            return "O comando demorou demasiado e foi cancelado após 30 segundos."
        except Exception as e:
            return f"Erro fatal a executar comando: {str(e)}"

    def play_music(self, song_name: str):
        """Abre o Spotify para tocar uma música. Usa pesquisa no Spotify."""
        try:
            import urllib.parse
            query = urllib.parse.quote(song_name)
            spotify_url = f"spotify:search:{query}"
            os.system(f'start "" "{spotify_url}"')
            return f"Sucesso! O Spotify foi aberto para pesquisar: '{song_name}'."
        except Exception as e:
            return f"Erro ao tentar tocar a música '{song_name}' no Spotify: {str(e)}"

    def listar_processos(self):
        """Lista os processos em execução no sistema com o consumo de CPU e memória."""
        try:
            result = subprocess.run(
                'powershell -Command "Get-Process | Sort-Object -Property WorkingSet64 -Descending | Select-Object -First 15 Name, Id, @{N=\'RAM_MB\';E={[math]::Round($_.WorkingSet64/1MB,1)}}, CPU | Format-Table -AutoSize"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            output = result.stdout.strip()
            if output:
                return f"Os 15 processos que mais consomem RAM:\n{output}"
            return "Não foi possível obter a lista de processos."
        except Exception as e:
            return f"Erro ao listar processos: {str(e)}"

    def matar_processo(self, nome: str):
        """Encerra um processo/programa à força pelo nome."""
        try:
            result = subprocess.run(
                f'taskkill /F /IM {nome}.exe',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return f"Processo '{nome}' encerrado com sucesso."
            else:
                # Tentar sem .exe
                result2 = subprocess.run(
                    f'taskkill /F /IM {nome}',
                    shell=True, capture_output=True, text=True, timeout=10
                )
                if result2.returncode == 0:
                    return f"Processo '{nome}' encerrado com sucesso."
                return f"Não encontrei o processo '{nome}' em execução."
        except Exception as e:
            return f"Erro ao matar processo: {str(e)}"

    def info_sistema(self):
        """Obtém informações detalhadas sobre o sistema: CPU, RAM, GPU, disco."""
        try:
            info_parts = []
            
            # CPU
            cpu_result = subprocess.run(
                'powershell -Command "(Get-WmiObject Win32_Processor).Name"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if cpu_result.stdout.strip():
                info_parts.append(f"CPU: {cpu_result.stdout.strip()}")
            
            # RAM
            ram_result = subprocess.run(
                'powershell -Command "$os = Get-WmiObject Win32_OperatingSystem; $total = [math]::Round($os.TotalVisibleMemorySize/1MB,1); $livre = [math]::Round($os.FreePhysicalMemory/1MB,1); $usada = $total - $livre; Write-Output \\"RAM Total: ${total}GB | Usada: ${usada}GB | Livre: ${livre}GB\\""',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if ram_result.stdout.strip():
                info_parts.append(ram_result.stdout.strip())
            
            # Disco
            disco_result = subprocess.run(
                'powershell -Command "Get-PSDrive -PSProvider FileSystem | ForEach-Object { $total = [math]::Round(($_.Used + $_.Free)/1GB,1); $livre = [math]::Round($_.Free/1GB,1); Write-Output \\"Disco $($_.Name): Total ${total}GB | Livre: ${livre}GB\\" }"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if disco_result.stdout.strip():
                info_parts.append(disco_result.stdout.strip())
            
            # GPU
            gpu_result = subprocess.run(
                'powershell -Command "(Get-WmiObject Win32_VideoController).Name"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if gpu_result.stdout.strip():
                info_parts.append(f"GPU: {gpu_result.stdout.strip()}")
            
            return "\n".join(info_parts) if info_parts else "Não foi possível obter informações do sistema."
        except Exception as e:
            return f"Erro ao obter informações: {str(e)}"

    def ajustar_volume(self, nivel: int):
        """Ajusta o volume do sistema de 0 a 100."""
        try:
            # Usar nircmd se disponível, senão PowerShell
            nivel = max(0, min(100, nivel))
            volume_hex = int(nivel / 100 * 65535)
            subprocess.run(
                f'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"',
                shell=True, capture_output=True, text=True, timeout=5
            )
            # Usar PowerShell com COM para definir volume
            subprocess.run(
                f'powershell -Command "Add-Type -TypeDefinition \'using System.Runtime.InteropServices; [Guid(\\"87CE5498-68D6-44E5-9215-6DA47EF883D8\\"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)] interface ISimpleAudioVolume {{ int SetMasterVolume(float fLevel, System.Guid EventContext); int GetMasterVolume(out float pfLevel); }};\'; $wshShell = New-Object -ComObject WScript.Shell; 1..50 | ForEach-Object {{ $wshShell.SendKeys([char]174) }}; 1..{nivel // 2} | ForEach-Object {{ $wshShell.SendKeys([char]175) }}"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            return f"Volume ajustado para aproximadamente {nivel}%."
        except Exception as e:
            return f"Erro ao ajustar volume: {str(e)}"

    def minimizar_tudo(self):
        """Minimiza todas as janelas abertas (mostra o Ambiente de Trabalho)."""
        try:
            subprocess.run(
                'powershell -Command "(New-Object -ComObject Shell.Application).MinimizeAll()"',
                shell=True, capture_output=True, text=True, timeout=5
            )
            return "Todas as janelas foram minimizadas."
        except Exception as e:
            return f"Erro ao minimizar: {str(e)}"

    def tirar_screenshot(self, caminho: str = None):
        """Tira uma captura de ecrã e guarda-a num ficheiro."""
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab(all_screens=True)
            if not caminho:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                caminho = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{timestamp}.png")
            screenshot.save(caminho)
            return f"Captura de ecrã guardada em: {caminho}"
        except Exception as e:
            return f"Erro ao tirar captura de ecrã: {str(e)}"

    def limpar_temporarios(self):
        """Limpa ficheiros temporários do sistema para libertar espaço."""
        try:
            temp_dirs = [
                os.environ.get('TEMP', ''),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
            ]
            ficheiros_apagados = 0
            espaco_libertado = 0
            
            for temp_dir in temp_dirs:
                if not temp_dir or not os.path.exists(temp_dir):
                    continue
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            tamanho = os.path.getsize(item_path)
                            os.remove(item_path)
                            ficheiros_apagados += 1
                            espaco_libertado += tamanho
                        elif os.path.isdir(item_path):
                            tamanho = sum(
                                os.path.getsize(os.path.join(dp, f))
                                for dp, dn, fn in os.walk(item_path)
                                for f in fn
                            )
                            shutil.rmtree(item_path, ignore_errors=True)
                            ficheiros_apagados += 1
                            espaco_libertado += tamanho
                    except (PermissionError, OSError):
                        continue
            
            mb = round(espaco_libertado / (1024 * 1024), 1)
            return f"Limpeza concluída! {ficheiros_apagados} ficheiros temporários apagados. Espaço libertado: {mb} MB."
        except Exception as e:
            return f"Erro durante a limpeza: {str(e)}"

    def alternar_janela(self, nome: str):
        try:
            import pygetwindow as gw
            janelas = gw.getWindowsWithTitle(nome)
            if not janelas:
                return f"Não encontrei nenhuma janela com o título '{nome}'."
            janela = janelas[0]
            janela.activate()
            return f"Janela '{janela.title}' ativada com sucesso."
        except Exception as e:
            return f"Erro ao alternar janela: {str(e)}"

    def maximizar_janela(self, nome: str = None):
        try:
            import pygetwindow as gw
            if nome:
                janelas = gw.getWindowsWithTitle(nome)
                if not janelas:
                    return f"Não encontrei nenhuma janela com '{nome}'."
                janela = janelas[0]
            else:
                janela = gw.getActiveWindow()
            if janela:
                janela.maximize()
                return f"Janela '{janela.title}' maximizada."
            return "Nenhuma janela ativa."
        except Exception as e:
            return f"Erro ao maximizar: {str(e)}"

    def organizar_janelas(self, nome_esquerda: str, nome_direita: str):
        try:
            import pygetwindow as gw
            import ctypes
            user32 = ctypes.windll.user32
            sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            
            esq = gw.getWindowsWithTitle(nome_esquerda)
            dir = gw.getWindowsWithTitle(nome_direita)
            
            if not esq or not dir:
                return "Não encontrei uma ou ambas as janelas para organizar."
                
            e, d = esq[0], dir[0]
            e.restore()
            d.restore()
            
            e.moveTo(0, 0)
            e.resizeTo(sw//2, sh)
            
            d.moveTo(sw//2, 0)
            d.resizeTo(sw//2, sh)
            
            return "Janelas organizadas lado-a-lado com sucesso."
        except Exception as e:
            return f"Erro ao organizar janelas: {str(e)}"

    def ler_area_transferencia(self):
        try:
            import pyperclip
            texto = pyperclip.paste()
            if not texto:
                return "A área de transferência está vazia."
            return f"Área de transferência:\n{texto}"
        except Exception as e:
            return f"Erro ao ler clipboard: {str(e)}"

    def escrever_area_transferencia(self, texto: str):
        try:
            import pyperclip
            pyperclip.copy(texto)
            return "Texto copiado para a área de transferência."
        except Exception as e:
            return f"Erro ao escrever clipboard: {str(e)}"

    def listar_janelas(self):
        try:
            import pygetwindow as gw
            titles = [w.title for w in gw.getWindowsWithTitle("") if w.title.strip() and w.visible]
            if not titles: return "Não há janelas abertas."
            return "Janelas abertas:\n" + "\n".join(f"- {t}" for t in set(titles))
        except Exception as e: return f"Erro ao listar janelas: {str(e)}"

    def fechar_janela(self, nome: str):
        """Fecha uma janela aberta pelo título."""
        try:
            import pygetwindow as gw
            janelas = gw.getWindowsWithTitle(nome)
            ram_result = subprocess.run(
                'powershell -Command "$os = Get-WmiObject Win32_OperatingSystem; $total = [math]::Round($os.TotalVisibleMemorySize/1MB,1); $livre = [math]::Round($os.FreePhysicalMemory/1MB,1); $usada = $total - $livre; Write-Output \\"RAM Total: ${total}GB | Usada: ${usada}GB | Livre: ${livre}GB\\""',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if ram_result.stdout.strip():
                info_parts.append(ram_result.stdout.strip())
            
            # Disco
            disco_result = subprocess.run(
                'powershell -Command "Get-PSDrive -PSProvider FileSystem | ForEach-Object { $total = [math]::Round(($_.Used + $_.Free)/1GB,1); $livre = [math]::Round($_.Free/1GB,1); Write-Output \\"Disco $($_.Name): Total ${total}GB | Livre: ${livre}GB\\" }"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if disco_result.stdout.strip():
                info_parts.append(disco_result.stdout.strip())
            
            # GPU
            gpu_result = subprocess.run(
                'powershell -Command "(Get-WmiObject Win32_VideoController).Name"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if gpu_result.stdout.strip():
                info_parts.append(f"GPU: {gpu_result.stdout.strip()}")
            
            return "\n".join(info_parts) if info_parts else "Não foi possível obter informações do sistema."
        except Exception as e:
            return f"Erro ao obter informações: {str(e)}"

    def minimizar_janela(self, nome: str):
        """Minimiza uma janela específica pelo título."""
        try:
            import pygetwindow as gw
            janelas = gw.getWindowsWithTitle(nome)
            if not janelas:
                return f"Não encontrei nenhuma janela com o título '{nome}' para minimizar."
            janela = janelas[0]
            janela.minimize()
            return f"Janela '{janela.title}' minimizada com sucesso."
        except Exception as e:
            return f"Erro ao minimizar janela: {str(e)}"
            
    def suspender_computador(self):
        """Coloca o computador em suspensão/hibernação."""
        try:
            import os
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "Comando de suspensão enviado ao sistema."
        except Exception as e:
            return f"Erro ao suspender computador: {str(e)}"
            
    def listar_programas_instalados(self):
        """Lista as aplicações instaladas no computador (varre os atalhos do Menu Iniciar)."""
        try:
            import os, glob
            start_menu_paths = [
                os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
                os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
            ]
            programas = set()
            for path in start_menu_paths:
                if not os.path.exists(path):
                    continue
                for shortcut in glob.glob(os.path.join(path, "**", "*.lnk"), recursive=True):
                    nome = os.path.basename(shortcut).replace(".lnk", "")
                    if "desinstalar" not in nome.lower() and "uninstall" not in nome.lower():
                        programas.add(nome)
            
            lista = sorted(list(programas))
            if not lista:
                return "Não foi possível encontrar programas instalados nos atalhos padrão."
            
            # Limitar a lista para não sobrecarregar o LLM
            return "Aplicações encontradas (principais):\n" + ", ".join(lista[:150])
        except Exception as e:
            return f"Erro ao listar programas: {str(e)}"
