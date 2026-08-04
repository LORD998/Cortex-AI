import datetime
import json
import os


class TaskManager:
    """Lembretes/tarefas com hora marcada, para a Cortex avisar proativamente."""

    def __init__(self, filename="lembretes_cortex.json"):
        self.filename = filename
        self.lembretes = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
        return []

    def _save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.lembretes, f, indent=4, ensure_ascii=False)

    def _next_id(self):
        return max((item["id"] for item in self.lembretes), default=0) + 1

    def criar_lembrete(self, texto: str, quando: str):
        """quando deve estar no formato 'AAAA-MM-DD HH:MM'."""
        texto = texto.strip()
        if not texto:
            return "Preciso de um texto para o lembrete."
        try:
            momento = datetime.datetime.strptime(quando.strip(), "%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            return f"Formato de data/hora inválido: '{quando}'. Usa 'AAAA-MM-DD HH:MM'."

        item = {
            "id": self._next_id(),
            "texto": texto,
            "quando": momento.strftime("%Y-%m-%d %H:%M"),
            "criado_em": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "concluido": False,
            "notificado": False,
        }
        self.lembretes.append(item)
        self._save()
        return f"Lembrete criado (#{item['id']}): '{texto}' para {item['quando']}."

    def listar_lembretes(self, incluir_concluidos: bool = False):
        pendentes = [
            item for item in self.lembretes
            if incluir_concluidos or not item["concluido"]
        ]
        if not pendentes:
            return "Não tens lembretes pendentes."
        pendentes = sorted(pendentes, key=lambda item: item["quando"])
        linhas = [
            f"#{item['id']} [{item['quando']}] {item['texto']}"
            + (" (concluído)" if item["concluido"] else "")
            for item in pendentes
        ]
        return "; ".join(linhas)

    def _encontrar(self, referencia: str):
        referencia = str(referencia).strip()
        sem_cardinal = referencia.lstrip("#")
        if sem_cardinal.isdigit():
            alvo_id = int(sem_cardinal)
            for item in self.lembretes:
                if item["id"] == alvo_id:
                    return item
            return None
        referencia_normalizada = referencia.casefold()
        candidatos = [
            item for item in self.lembretes
            if not item["concluido"] and referencia_normalizada in item["texto"].casefold()
        ]
        return candidatos[0] if candidatos else None

    def concluir_lembrete(self, referencia: str):
        item = self._encontrar(referencia)
        if not item:
            return f"Não encontrei nenhum lembrete correspondente a '{referencia}'."
        item["concluido"] = True
        self._save()
        return f"Lembrete #{item['id']} marcado como concluído: '{item['texto']}'."

    def cancelar_lembrete(self, referencia: str):
        item = self._encontrar(referencia)
        if not item:
            return f"Não encontrei nenhum lembrete correspondente a '{referencia}'."
        self.lembretes.remove(item)
        self._save()
        return f"Lembrete #{item['id']} cancelado: '{item['texto']}'."

    def obter_vencidos(self):
        """Lembretes cuja hora já passou, ainda não concluídos nem notificados."""
        agora = datetime.datetime.now()
        vencidos = []
        for item in self.lembretes:
            if item["concluido"] or item["notificado"]:
                continue
            try:
                momento = datetime.datetime.strptime(item["quando"], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if momento <= agora:
                vencidos.append(item)
        return vencidos

    def marcar_notificados(self, ids):
        ids = set(ids)
        for item in self.lembretes:
            if item["id"] in ids:
                item["notificado"] = True
        self._save()

    @staticmethod
    def formatar_aviso(itens):
        if len(itens) == 1:
            return f"Lembrete: {itens[0]['texto']}."
        textos = "; ".join(item["texto"] for item in itens)
        return f"Tens {len(itens)} lembretes: {textos}."
