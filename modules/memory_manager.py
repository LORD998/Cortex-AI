import json
import os
import datetime
import difflib

class MemoryManager:
    def __init__(self, filename="memoria_cortex.json"):
        self.filename = filename
        self.memory = self._load()

    def _load(self):
        data = {"fatos": [], "aprendizagens": [], "historico_apps": []}
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Migrar ficheiro antigo: garantir que todas as chaves existem
                    for key in data:
                        if key in loaded:
                            data[key] = loaded[key]
            except:
                pass
        # Migrar fatos antigos (strings simples) para o novo formato com data
        data["fatos"] = [
            f if isinstance(f, dict) else {"texto": f, "data": ""}
            for f in data["fatos"]
        ]
        return data

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=4, ensure_ascii=False)

    def _e_parecido(self, a: str, b: str, limiar: float = 0.82) -> bool:
        """Deteta duplicados e quase-duplicados (ex: 'alemão' vs 'aprender alemão')."""
        return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio() >= limiar

    def guardar_memoria(self, fato: str):
        """Guarda um novo fato sobre o utilizador na memória a longo prazo, evitando duplicados e quase-duplicados."""
        fato = fato.strip()
        if not fato:
            return "Fato vazio, nada a guardar."
        for existente in self.memory["fatos"]:
            if self._e_parecido(existente["texto"], fato):
                return "Já sabia disso."
        self.memory["fatos"].append({
            "texto": fato,
            "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        # Manter apenas os últimos 100 fatos
        if len(self.memory["fatos"]) > 100:
            self.memory["fatos"] = self.memory["fatos"][-100:]
        self._save()
        return f"Sucesso: Memorizei que '{fato}'."

    def aprender(self, topico: str, conteudo: str):
        """Armazena conhecimento novo. Se já existir um tópico/conteúdo parecido, atualiza-o em vez de duplicar."""
        topico = topico.strip()
        conteudo = conteudo.strip()[:1000]
        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for entrada in self.memory["aprendizagens"]:
            if self._e_parecido(entrada["topico"], topico) or self._e_parecido(entrada["conteudo"], conteudo):
                entrada["topico"] = topico
                entrada["conteudo"] = conteudo
                entrada["data"] = agora
                self._save()
                return f"Conhecimento sobre '{topico}' atualizado."

        self.memory["aprendizagens"].append({"topico": topico, "conteudo": conteudo, "data": agora})
        # Manter apenas as últimas 50 aprendizagens
        if len(self.memory["aprendizagens"]) > 50:
            self.memory["aprendizagens"] = self.memory["aprendizagens"][-50:]
        self._save()
        return f"Conhecimento armazenado sobre '{topico}'."

    def registar_uso_app(self, app_name: str):
        """Regista qual programa o utilizador abriu para aprender os seus hábitos."""
        self.memory["historico_apps"].append({
            "app": app_name,
            "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        # Manter últimos 100 registos
        if len(self.memory["historico_apps"]) > 100:
            self.memory["historico_apps"] = self.memory["historico_apps"][-100:]
        self._save()

    def obter_apps_favoritas(self):
        """Analisa o histórico e devolve as apps mais usadas pelo utilizador."""
        if not self.memory["historico_apps"]:
            return "Ainda não tenho dados suficientes sobre os teus hábitos."
        from collections import Counter
        apps = [r["app"] for r in self.memory["historico_apps"]]
        top = Counter(apps).most_common(5)
        return "Apps mais usadas: " + ", ".join([f"{app} ({count}x)" for app, count in top])

    def relembrar(self):
        """Retorna um resumo compacto dos factos e conhecimento acumulado, com conteúdo real (não só rótulos)."""
        partes = []
        if self.memory.get("fatos"):
            ultimos_fatos = [f["texto"] for f in self.memory["fatos"][-6:]]
            partes.append("Factos sobre o utilizador: " + "; ".join(ultimos_fatos))
        if self.memory.get("aprendizagens"):
            ultimas = self.memory["aprendizagens"][-4:]
            resumo = "; ".join(f"{a['topico']}: {a['conteudo'][:100]}" for a in ultimas)
            partes.append("Conhecimento recente: " + resumo)

        return " | ".join(partes) if partes else ""
