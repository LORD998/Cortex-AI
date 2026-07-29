import os
import glob
import shutil
import datetime

class FileManager:
    def __init__(self):
        # Mapeamento de extensões para categorias (para organização automática)
        self.categorias = {
            "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"],
            "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
            "Musica": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
            "Documentos": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".odt", ".rtf"],
            "Codigo": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h", ".json", ".xml", ".yaml", ".yml", ".md", ".sql", ".sh", ".bat", ".ps1"],
            "Comprimidos": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "Instaladores": [".exe", ".msi", ".dmg", ".deb", ".rpm"],
            "Fontes": [".ttf", ".otf", ".woff", ".woff2"],
        }

    def list_current_directory(self):
        """Lista o conteúdo do diretório atual."""
        try:
            files = os.listdir('.')
            if not files:
                return "O diretório atual está vazio."
            return "Ficheiros no diretório atual:\n" + "\n".join(f"- {f}" for f in files)
        except Exception as e:
            return f"Ocorreu um erro ao tentar listar os ficheiros: {str(e)}"

    def procurar_ficheiros(self, nome: str, diretorio_base: str = None):
        """Procura ficheiros recursivamente a partir de um diretório base."""
        try:
            diretorio_base = diretorio_base or os.path.join(os.path.expanduser("~"), "Desktop")
            padrao = os.path.join(diretorio_base, "**", f"*{nome}*")
            resultados = glob.glob(padrao, recursive=True)
            if not resultados:
                return f"Não encontrei nenhum ficheiro com '{nome}' no diretório '{diretorio_base}'."
            # Limitar a 15 resultados para não sobrecarregar o contexto
            res_lista = "\n".join(f"- {f}" for f in resultados[:15])
            if len(resultados) > 15:
                res_lista += f"\n... e mais {len(resultados)-15} ficheiros."
            return f"Encontrei os seguintes ficheiros:\n{res_lista}"
        except Exception as e:
            return f"Erro ao procurar: {str(e)}"

    def ler_ficheiro(self, caminho: str):
        """Lê o conteúdo de um ficheiro de texto."""
        try:
            if not os.path.exists(caminho):
                return f"O ficheiro '{caminho}' não existe."
            tamanho = os.path.getsize(caminho)
            if tamanho > 500000:  # 500KB
                return f"O ficheiro '{caminho}' é demasiado grande ({round(tamanho/1024)}KB). Só consigo ler ficheiros até 500KB."
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read(3000)  # Ler no máximo 3000 caracteres
            truncado = " (truncado a 3000 caracteres)" if len(conteudo) >= 3000 else ""
            return f"Conteúdo de '{caminho}'{truncado}:\n{conteudo}"
        except Exception as e:
            return f"Erro ao ler o ficheiro: {str(e)}"

    def escrever_ficheiro(self, caminho: str, conteudo: str):
        """Escreve texto num ficheiro, criando-o se não existir."""
        try:
            # Criar diretórios necessários
            pasta = os.path.dirname(caminho)
            if pasta and not os.path.exists(pasta):
                os.makedirs(pasta, exist_ok=True)
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            return f"Ficheiro '{caminho}' guardado com sucesso!"
        except Exception as e:
            return f"Erro ao escrever o ficheiro: {str(e)}"

    def criar_pasta(self, caminho: str):
        """Cria uma pasta (e sub-pastas) no disco."""
        try:
            os.makedirs(caminho, exist_ok=True)
            return f"Pasta '{caminho}' criada com sucesso!"
        except Exception as e:
            return f"Erro ao criar pasta: {str(e)}"

    def mover_ficheiro(self, origem: str, destino: str):
        """Move um ficheiro ou pasta de um local para outro."""
        try:
            if not os.path.exists(origem):
                return f"O ficheiro/pasta '{origem}' não existe."
            # Se o destino é uma pasta, mover para dentro
            if os.path.isdir(destino):
                nome = os.path.basename(origem)
                destino = os.path.join(destino, nome)
            shutil.move(origem, destino)
            return f"Movido com sucesso: '{origem}' → '{destino}'."
        except Exception as e:
            return f"Erro ao mover: {str(e)}"

    def copiar_ficheiro(self, origem: str, destino: str):
        """Copia um ficheiro ou pasta."""
        try:
            if not os.path.exists(origem):
                return f"O ficheiro/pasta '{origem}' não existe."
            if os.path.isdir(origem):
                shutil.copytree(origem, destino)
            else:
                # Se destino é pasta, copiar para dentro
                if os.path.isdir(destino):
                    destino = os.path.join(destino, os.path.basename(origem))
                shutil.copy2(origem, destino)
            return f"Copiado com sucesso: '{origem}' → '{destino}'."
        except Exception as e:
            return f"Erro ao copiar: {str(e)}"

    def renomear_ficheiro(self, caminho: str, novo_nome: str):
        """Renomeia um ficheiro ou pasta."""
        try:
            if not os.path.exists(caminho):
                return f"O ficheiro/pasta '{caminho}' não existe."
            pasta = os.path.dirname(caminho)
            novo_caminho = os.path.join(pasta, novo_nome)
            os.rename(caminho, novo_caminho)
            return f"Renomeado com sucesso: '{os.path.basename(caminho)}' → '{novo_nome}'."
        except Exception as e:
            return f"Erro ao renomear: {str(e)}"

    def apagar_ficheiro(self, caminho: str):
        """Apaga um ficheiro ou pasta do disco."""
        try:
            if not os.path.exists(caminho):
                return f"O ficheiro/pasta '{caminho}' não existe."
            if os.path.isdir(caminho):
                shutil.rmtree(caminho)
                return f"Pasta '{caminho}' e todo o seu conteúdo apagados com sucesso."
            else:
                os.remove(caminho)
                return f"Ficheiro '{caminho}' apagado com sucesso."
        except Exception as e:
            return f"Erro ao apagar: {str(e)}"

    def organizar_pasta(self, caminho: str):
        """Organiza automaticamente os ficheiros de uma pasta por tipo (imagens, vídeos, docs, etc.)."""
        try:
            if not os.path.exists(caminho) or not os.path.isdir(caminho):
                return f"A pasta '{caminho}' não existe."
            
            ficheiros = [f for f in os.listdir(caminho) if os.path.isfile(os.path.join(caminho, f))]
            if not ficheiros:
                return f"A pasta '{caminho}' não tem ficheiros para organizar."
            
            movidos = 0
            for ficheiro in ficheiros:
                ext = os.path.splitext(ficheiro)[1].lower()
                categoria_destino = None
                
                for categoria, extensoes in self.categorias.items():
                    if ext in extensoes:
                        categoria_destino = categoria
                        break
                
                if categoria_destino:
                    pasta_destino = os.path.join(caminho, categoria_destino)
                    os.makedirs(pasta_destino, exist_ok=True)
                    origem = os.path.join(caminho, ficheiro)
                    destino = os.path.join(pasta_destino, ficheiro)
                    # Evitar conflitos de nome
                    if os.path.exists(destino):
                        nome, ext_f = os.path.splitext(ficheiro)
                        timestamp = datetime.datetime.now().strftime("%H%M%S")
                        destino = os.path.join(pasta_destino, f"{nome}_{timestamp}{ext_f}")
                    shutil.move(origem, destino)
                    movidos += 1
            
            return f"Organização concluída! {movidos} ficheiros organizados em categorias dentro de '{caminho}'."
        except Exception as e:
            return f"Erro ao organizar: {str(e)}"

    def listar_pasta(self, caminho: str):
        """Lista o conteúdo detalhado de uma pasta."""
        try:
            if not os.path.exists(caminho):
                return f"A pasta '{caminho}' não existe."
            
            itens = os.listdir(caminho)
            if not itens:
                return f"A pasta '{caminho}' está vazia."
            
            resultado = []
            pastas = []
            ficheiros = []
            
            for item in sorted(itens):
                caminho_completo = os.path.join(caminho, item)
                if os.path.isdir(caminho_completo):
                    num_itens = len(os.listdir(caminho_completo))
                    pastas.append(f"📁 {item}/ ({num_itens} itens)")
                else:
                    tamanho = os.path.getsize(caminho_completo)
                    if tamanho > 1024 * 1024:
                        tam_str = f"{round(tamanho / (1024*1024), 1)} MB"
                    elif tamanho > 1024:
                        tam_str = f"{round(tamanho / 1024, 1)} KB"
                    else:
                        tam_str = f"{tamanho} bytes"
                    ficheiros.append(f"📄 {item} ({tam_str})")
            
            resultado = pastas + ficheiros
            return f"Conteúdo de '{caminho}':\n" + "\n".join(resultado[:30])
        except Exception as e:
            return f"Erro ao listar pasta: {str(e)}"

    def descompactar_zip(self, ficheiro: str, destino: str = None):
        try:
            import zipfile
            if not os.path.exists(ficheiro):
                return f"O ficheiro '{ficheiro}' não existe."
            if not destino:
                destino = os.path.splitext(ficheiro)[0]
            os.makedirs(destino, exist_ok=True)
            with zipfile.ZipFile(ficheiro, 'r') as zip_ref:
                destino_real = os.path.realpath(destino)
                for member in zip_ref.infolist():
                    member_path = os.path.realpath(os.path.join(destino, member.filename))
                    if os.path.commonpath([destino_real, member_path]) != destino_real:
                        return f"Erro: o ZIP contém um caminho inseguro: {member.filename}"
                zip_ref.extractall(destino)
            return f"Ficheiro ZIP extraído com sucesso para: '{destino}'."
        except Exception as e:
            return f"Erro ao descompactar: {str(e)}"

    def criar_backup(self, pasta: str):
        try:
            import shutil
            import os
            import datetime
            if not os.path.exists(pasta):
                return f"A pasta '{pasta}' não existe."
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_backup = f"{os.path.basename(pasta)}_backup_{timestamp}"
            caminho_base = os.path.join(os.path.dirname(pasta), nome_backup)
            shutil.make_archive(caminho_base, 'zip', pasta)
            return f"Backup criado com sucesso: '{caminho_base}.zip'."
        except Exception as e:
            return f"Erro ao criar backup: {str(e)}"

    def encontrar_duplicados(self, pasta: str):
        try:
            import hashlib
            if not os.path.exists(pasta):
                return f"A pasta '{pasta}' não existe."
                
            hashes = {}
            grupos = {}
            
            for root, dirs, files in os.walk(pasta):
                for nome in files:
                    caminho = os.path.join(root, nome)
                    try:
                        digest = hashlib.sha256()
                        with open(caminho, 'rb') as f:
                            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                                digest.update(chunk)
                        file_hash = digest.hexdigest()
                        if file_hash in hashes:
                            grupos.setdefault(file_hash, [hashes[file_hash]]).append(caminho)
                        else:
                            hashes[file_hash] = caminho
                    except (PermissionError, OSError):
                        pass
                        
            if not grupos:
                return "Não foram encontrados ficheiros duplicados."
            linhas = []
            for indice, caminhos in enumerate(grupos.values(), start=1):
                linhas.append(f"Grupo {indice}:")
                linhas.extend(f"- {caminho}" for caminho in caminhos)
            return (
                f"Encontrei {len(grupos)} grupos de duplicados. "
                "Nenhum ficheiro foi apagado.\n" + "\n".join(linhas[:100])
            )
        except Exception as e:
            return f"Erro ao procurar duplicados: {str(e)}"

    def abrir_ficheiro(self, caminho: str):
        """Abre um ficheiro com o programa padrão do Windows."""
        try:
            import os
            if not os.path.exists(caminho):
                return f"O ficheiro '{caminho}' não existe."
            os.startfile(caminho)
            return f"Ficheiro '{os.path.basename(caminho)}' aberto com sucesso."
        except Exception as e:
            return f"Erro ao abrir ficheiro: {str(e)}"

    def ler_pdf_docx(self, caminho: str):
        """Lê texto nativo de PDFs e documentos Word para evitar usar OCR."""
        try:
            import os
            if not os.path.exists(caminho):
                return f"O ficheiro '{caminho}' não existe."
                
            ext = caminho.lower().split('.')[-1]
            texto = ""
            
            if ext == "pdf":
                try:
                    from pypdf import PdfReader
                    with open(caminho, "rb") as f:
                        reader = PdfReader(f)
                        texto = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                except ImportError:
                    return "A biblioteca pypdf não está instalada. Instale as dependências do projeto."
            elif ext in ["docx", "doc"]:
                if ext == "doc":
                    return "O formato DOC antigo não é suportado localmente. Converte-o para DOCX."
                try:
                    from docx import Document
                    documento = Document(caminho)
                    texto = "\n".join(paragrafo.text for paragrafo in documento.paragraphs)
                except ImportError:
                    return "A biblioteca python-docx não está instalada. Instale as dependências do projeto."
            else:
                return "Formato não suportado por esta ferramenta. Tenta 'ler_ficheiro' normal."
                
            return f"Conteúdo do Documento:\n{texto[:5000]}" # Limitar a 5000 caracteres
        except Exception as e:
            return f"Erro ao extrair texto do documento: {str(e)}"
            
    def compactar_zip(self, caminho: str, destino_zip: str):
        """Cria um arquivo ZIP de um ficheiro ou pasta."""
        try:
            import shutil, os
            if not os.path.exists(caminho):
                return f"O caminho '{caminho}' não existe."
                
            # shutil.make_archive adiciona .zip automaticamente
            if destino_zip.endswith('.zip'):
                destino_zip = destino_zip[:-4]
                
            shutil.make_archive(destino_zip, 'zip', caminho)
            return f"Ficheiros compactados com sucesso em '{destino_zip}.zip'."
        except Exception as e:
            return f"Erro ao compactar: {str(e)}"
