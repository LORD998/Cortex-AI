import os
import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path

from core.config import CortexConfig
from core.orchestrator import CortexOrchestrator
from core.tool_router import ToolRouter
from modules.email_manager import EmailManager
from modules.file_manager import FileManager


class FakeNLP:
    def __init__(self, messages):
        self.messages = list(messages)
        self.calls = []

    def process_with_tools(self, history, tools=None, think=False):
        self.calls.append(
            {
                "history": list(history),
                "tools": list(tools or []),
                "think": think,
            }
        )
        return self.messages.pop(0)


class FakeOSManager:
    def __init__(self):
        self.time_calls = 0

    def get_current_time(self):
        self.time_calls += 1
        return "Agora são 14:30."


class FakeEmailManager:
    def __init__(self):
        self.sent = []

    def enviar_email(self, destinatario, assunto, corpo, anexo=None):
        self.sent.append((destinatario, assunto, corpo, anexo))
        return f"E-mail enviado para {destinatario}."


def test_config():
    return replace(
        CortexConfig.from_env(),
        max_agent_steps=4,
        max_history_messages=10,
        max_tools_per_request=18,
    )


class ToolRouterTests(unittest.TestCase):
    def test_email_request_only_receives_email_tools(self):
        schemas = [
            {"type": "function", "function": {"name": name}}
            for name in (
                "listar_emails",
                "ler_email",
                "criar_rascunho_email",
                "responder_email",
                "enviar_email",
                "info_sistema",
            )
        ]
        selected = ToolRouter().select(
            "Mostra o último email e prepara uma resposta",
            schemas,
        )
        names = {item["function"]["name"] for item in selected}
        self.assertEqual(
            names,
            {
                "listar_emails",
                "ler_email",
                "criar_rascunho_email",
                "responder_email",
                "enviar_email",
            },
        )


class OrchestratorTests(unittest.TestCase):
    def test_agent_executes_tool_then_checks_result(self):
        nlp = FakeNLP(
            [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_current_time",
                                "arguments": {},
                            }
                        }
                    ],
                },
                {"role": "assistant", "content": "Agora são 14:30."},
            ]
        )
        orchestrator = CortexOrchestrator(nlp=nlp, config=test_config())
        os_manager = FakeOSManager()
        orchestrator.load_module("os_manager", os_manager)

        response = orchestrator.process_command("Que horas são?")

        self.assertEqual(response, "Agora são 14:30.")
        self.assertEqual(os_manager.time_calls, 1)
        self.assertEqual(len(nlp.calls), 2)
        tool_names = {
            schema["function"]["name"] for schema in nlp.calls[0]["tools"]
        }
        self.assertIn("get_current_time", tool_names)
        self.assertLess(len(tool_names), 15)

    def test_email_send_waits_for_confirmation(self):
        nlp = FakeNLP(
            [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "enviar_email",
                                "arguments": {
                                    "destinatario": "ana@example.com",
                                    "assunto": "Reunião",
                                    "corpo": "Confirmado.",
                                },
                            }
                        }
                    ],
                }
            ]
        )
        orchestrator = CortexOrchestrator(nlp=nlp, config=test_config())
        email_manager = FakeEmailManager()
        orchestrator.load_module("email_manager", email_manager)

        warning = orchestrator.process_command(
            "Envia um email para a Ana a confirmar a reunião"
        )
        self.assertIn("confirmação", warning)
        self.assertEqual(email_manager.sent, [])

        result = orchestrator.process_command("confirmo")
        self.assertIn("enviado", result)
        self.assertEqual(len(email_manager.sent), 1)

    def test_reasoning_is_automatic_and_keeps_simple_requests_fast(self):
        simple_nlp = FakeNLP(
            [{"role": "assistant", "content": "Olá.", "tool_calls": []}]
        )
        simple = CortexOrchestrator(nlp=simple_nlp, config=test_config())
        simple.process_command("Olá, tudo bem?")
        self.assertFalse(simple_nlp.calls[0]["think"])

        complex_nlp = FakeNLP(
            [{"role": "assistant", "content": "Plano pronto.", "tool_calls": []}]
        )
        complex_agent = CortexOrchestrator(nlp=complex_nlp, config=test_config())
        complex_agent.process_command(
            "Analisa este problema e cria um plano passo a passo para o resolver."
        )
        self.assertTrue(complex_nlp.calls[0]["think"])


class FileManagerTests(unittest.TestCase):
    def test_duplicate_scan_never_deletes_files(self):
        manager = FileManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir, "a.txt")
            second = Path(temp_dir, "b.txt")
            first.write_text("igual", encoding="utf-8")
            second.write_text("igual", encoding="utf-8")

            result = manager.encontrar_duplicados(temp_dir)

            self.assertIn("Nenhum ficheiro foi apagado", result)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())

    def test_zip_path_traversal_is_blocked(self):
        manager = FileManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir, "bad.zip")
            destination = Path(temp_dir, "out")
            escaped = Path(temp_dir, "escaped.txt")
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("../escaped.txt", "não deve sair")

            result = manager.descompactar_zip(str(archive), str(destination))

            self.assertIn("caminho inseguro", result)
            self.assertFalse(escaped.exists())


class EmailManagerTests(unittest.TestCase):
    def test_missing_credentials_has_clear_error(self):
        manager = EmailManager(credentials_path=os.path.join("Z:\\", "missing.json"))
        result = manager.listar_mensagens()
        self.assertIn("Credenciais Gmail não encontradas", result)


if __name__ == "__main__":
    unittest.main()
