import os
import subprocess
import shutil

class DevManager:
    def __init__(self):
        self.name = "DevManager"

    def criar_projeto_python(self, nome: str, caminho: str = None):
        """Cria um projeto Python completo com ambiente virtual."""
        try:
            caminho = caminho or os.path.join(os.path.expanduser("~"), "Desktop")
            base = os.path.join(caminho, nome)
            os.makedirs(base, exist_ok=True)
            
            # Criar ficheiros base
            with open(os.path.join(base, "main.py"), "w", encoding="utf-8") as f:
                f.write('def main():\n    print("Olá, Mundo!")\n\nif __name__ == "__main__":\n    main()\n')
            
            with open(os.path.join(base, "requirements.txt"), "w", encoding="utf-8") as f:
                f.write("# Adiciona as tuas dependências aqui\n")
            
            # Criar venv
            subprocess.run(["python", "-m", "venv", os.path.join(base, "venv")], cwd=base, creationflags=subprocess.CREATE_NO_WINDOW)
            
            return f"Projeto Python '{nome}' criado com sucesso em: {base}"
        except Exception as e:
            return f"Erro ao criar projeto Python: {str(e)}"

    def criar_projeto_web(self, nome: str, caminho: str = None):
        """Cria um projeto Web básico (HTML/CSS/JS)."""
        try:
            caminho = caminho or os.path.join(os.path.expanduser("~"), "Desktop")
            base = os.path.join(caminho, nome)
            os.makedirs(base, exist_ok=True)
            
            with open(os.path.join(base, "index.html"), "w", encoding="utf-8") as f:
                f.write('<!DOCTYPE html>\n<html lang="pt">\n<head>\n    <meta charset="UTF-8">\n    <title>'+nome+'</title>\n    <link rel="stylesheet" href="style.css">\n</head>\n<body>\n    <h1>Olá, Mundo!</h1>\n    <script src="script.js"></script>\n</body>\n</html>')
            
            with open(os.path.join(base, "style.css"), "w", encoding="utf-8") as f:
                f.write('body {\n    font-family: Arial, sans-serif;\n    display: flex;\n    justify-content: center;\n    align-items: center;\n    height: 100vh;\n    background-color: #222;\n    color: white;\n}')
            
            with open(os.path.join(base, "script.js"), "w", encoding="utf-8") as f:
                f.write('console.log("Sistema iniciado.");')
            
            return f"Projeto Web '{nome}' criado com sucesso em: {base}"
        except Exception as e:
            return f"Erro ao criar projeto Web: {str(e)}"
