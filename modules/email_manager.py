import base64
import json
import mimetypes
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


class EmailManager:
    """Gestão de Gmail com leitura, rascunhos, respostas e envio explícito."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    def __init__(self, credentials_path: str | None = None):
        self.service = None
        configured = credentials_path or os.getenv("CORTEX_GMAIL_CREDENTIALS")
        candidates = [
            configured,
            os.path.join(os.getenv("APPDATA", ""), "Cortex", "gmail_credentials.json"),
            os.path.expanduser("~/.gemini/antigravity/gmail_credentials.json"),
        ]
        self.credentials_path = next(
            (path for path in candidates if path and os.path.isfile(path)),
            configured or candidates[1],
        )

    def _init_service(self):
        if self.service is not None:
            return None
        if not self.credentials_path or not os.path.isfile(self.credentials_path):
            return (
                "Credenciais Gmail não encontradas. Define CORTEX_GMAIL_CREDENTIALS "
                "com o caminho do ficheiro OAuth autorizado."
            )
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials.from_authorized_user_file(
                self.credentials_path,
                self.SCOPES,
            )
            self.service = build("gmail", "v1", credentials=creds, cache_discovery=False)
            return None
        except Exception as exc:
            return f"Erro ao iniciar Gmail API: {exc}"

    def _ensure_service(self):
        error = self._init_service()
        return error

    @staticmethod
    def _headers(payload: dict) -> dict:
        return {
            header.get("name", "").casefold(): header.get("value", "")
            for header in payload.get("headers", [])
        }

    @classmethod
    def _extract_text(cls, payload: dict) -> str:
        mime_type = payload.get("mimeType", "")
        data = payload.get("body", {}).get("data")
        if data and mime_type in {"text/plain", "text/html"}:
            try:
                decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
                return decoded.decode("utf-8", errors="replace")
            except Exception:
                return ""

        plain_parts = []
        html_parts = []
        for part in payload.get("parts", []) or []:
            text = cls._extract_text(part)
            if not text:
                continue
            if part.get("mimeType") == "text/plain":
                plain_parts.append(text)
            else:
                html_parts.append(text)
        return "\n".join(plain_parts or html_parts)

    @staticmethod
    def _build_message(
        to: str,
        subject: str,
        body: str,
        attachment_path: str | None = None,
    ) -> MIMEMultipart:
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))

        if attachment_path:
            path = Path(attachment_path).expanduser()
            if not path.is_file():
                raise FileNotFoundError(f"O anexo não existe: {path}")
            content_type, encoding = mimetypes.guess_type(str(path))
            if content_type is None or encoding is not None:
                content_type = "application/octet-stream"
            main_type, sub_type = content_type.split("/", 1)
            with path.open("rb") as handle:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(handle.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=path.name,
            )
            message.attach(attachment)
        return message

    @staticmethod
    def _raw_message(message: MIMEMultipart) -> str:
        return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")

    def listar_mensagens(self, max_results: int = 5):
        error = self._ensure_service()
        if error:
            return error
        try:
            max_results = max(1, min(int(max_results), 25))
            result = self.service.users().messages().list(
                userId="me",
                maxResults=max_results,
            ).execute()
            summaries = []
            for item in result.get("messages", []):
                detail = self.service.users().messages().get(
                    userId="me",
                    id=item["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()
                headers = self._headers(detail.get("payload", {}))
                summaries.append(
                    {
                        "id": item["id"],
                        "remetente": headers.get("from", "Desconhecido"),
                        "assunto": headers.get("subject", "Sem assunto"),
                        "data": headers.get("date", "Desconhecida"),
                        "resumo": detail.get("snippet", ""),
                    }
                )
            return json.dumps(summaries, ensure_ascii=False)
        except Exception as exc:
            return f"Erro ao listar e-mails: {exc}"

    def ler_mensagem(self, mensagem_id: str):
        error = self._ensure_service()
        if error:
            return error
        if not mensagem_id:
            return "Erro: falta o ID do e-mail."
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=mensagem_id,
                format="full",
            ).execute()
            payload = message.get("payload", {})
            headers = self._headers(payload)
            body = self._extract_text(payload).strip() or message.get("snippet", "")
            return json.dumps(
                {
                    "id": mensagem_id,
                    "thread_id": message.get("threadId"),
                    "remetente": headers.get("from", ""),
                    "destinatario": headers.get("to", ""),
                    "assunto": headers.get("subject", "Sem assunto"),
                    "data": headers.get("date", ""),
                    "corpo": body[:20000],
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            return f"Erro ao ler e-mail {mensagem_id}: {exc}"

    def criar_rascunho(
        self,
        destinatario: str,
        assunto: str,
        corpo: str,
        anexo_caminho: str | None = None,
    ):
        error = self._ensure_service()
        if error:
            return error
        if not destinatario or not corpo:
            return "Erro: destinatário e corpo são obrigatórios."
        try:
            message = self._build_message(
                destinatario,
                assunto,
                corpo,
                anexo_caminho,
            )
            draft = self.service.users().drafts().create(
                userId="me",
                body={"message": {"raw": self._raw_message(message)}},
            ).execute()
            return (
                f"Rascunho criado no Gmail para {destinatario} "
                f"(ID: {draft.get('id', 'desconhecido')}). Não foi enviado."
            )
        except Exception as exc:
            return f"Erro ao criar rascunho: {exc}"

    def criar_rascunho_resposta(self, mensagem_id: str, corpo: str):
        error = self._ensure_service()
        if error:
            return error
        if not mensagem_id or not corpo:
            return "Erro: ID do e-mail e corpo da resposta são obrigatórios."
        try:
            original = self.service.users().messages().get(
                userId="me",
                id=mensagem_id,
                format="full",
            ).execute()
            headers = self._headers(original.get("payload", {}))
            subject = headers.get("subject", "Sem assunto")
            if not subject.casefold().startswith("re:"):
                subject = f"Re: {subject}"

            message = self._build_message(headers.get("from", ""), subject, corpo)
            original_message_id = headers.get("message-id", "")
            if original_message_id:
                message["In-Reply-To"] = original_message_id
                message["References"] = original_message_id

            draft = self.service.users().drafts().create(
                userId="me",
                body={
                    "message": {
                        "raw": self._raw_message(message),
                        "threadId": original.get("threadId"),
                    }
                },
            ).execute()
            return (
                f"Rascunho de resposta criado (ID: {draft.get('id', 'desconhecido')}). "
                "Não foi enviado."
            )
        except Exception as exc:
            return f"Erro ao preparar resposta: {exc}"

    def enviar_email(
        self,
        destinatario: str,
        assunto: str,
        corpo: str,
        anexo_caminho: str | None = None,
    ):
        error = self._ensure_service()
        if error:
            return error
        if not destinatario or not corpo:
            return "Erro: destinatário e corpo são obrigatórios."
        try:
            message = self._build_message(
                destinatario,
                assunto,
                corpo,
                anexo_caminho,
            )
            sent = self.service.users().messages().send(
                userId="me",
                body={"raw": self._raw_message(message)},
            ).execute()
            return (
                f"E-mail enviado para {destinatario} com o assunto “{assunto}” "
                f"(ID: {sent.get('id', 'desconhecido')})."
            )
        except Exception as exc:
            return f"Erro ao enviar e-mail: {exc}"
