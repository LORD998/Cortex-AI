import os
import subprocess
import json

class EmailManager:
    """Módulo para gerir Gmail via API (leitura, resumo, resposta, organização)."""
    def __init__(self):
        self.service = None  # será inicializado na primeira chamada

    def _init_service(self):
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            # Espera que as credenciais estejam em %APPDATA%/gmail_credentials.json
            cred_path = os.path.expanduser('~/.gemini/antigravity/gmail_credentials.json')
            if not os.path.exists(cred_path):
                return "Credenciais Gmail não encontradas. Por favor configure-as primeiro."
            creds = Credentials.from_authorized_user_file(cred_path, ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.modify'])
            self.service = build('gmail', 'v1', credentials=creds)
            return "Serviço Gmail inicializado."
        except Exception as e:
            return f"Erro ao iniciar Gmail API: {str(e)}"

    def listar_mensagens(self, max_results: int = 5):
        if not self.service:
            init_msg = self._init_service()
            if "Erro" in init_msg:
                return init_msg
        try:
            result = self.service.users().messages().list(userId='me', maxResults=max_results).execute()
            mensagens = result.get('messages', [])
            
            resumo_emails = []
            for msg in mensagens:
                # Obter detalhes do cabeçalho
                m_detalhe = self.service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From', 'Date']).execute()
                headers = m_detalhe.get('payload', {}).get('headers', [])
                
                assunto = "Sem Assunto"
                remetente = "Desconhecido"
                data = "Desconhecida"
                
                for h in headers:
                    if h['name'] == 'Subject': assunto = h['value']
                    if h['name'] == 'From': remetente = h['value']
                    if h['name'] == 'Date': data = h['value']
                    
                resumo_emails.append({
                    "id": msg['id'],
                    "remetente": remetente,
                    "assunto": assunto,
                    "data": data
                })
                
            return json.dumps(resumo_emails, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao listar e-mails: {str(e)}"

    def ler_mensagem(self, mensagem_id: str):
        if not self.service:
            init_msg = self._init_service()
            if "Erro" in init_msg:
                return init_msg
        try:
            msg = self.service.users().messages().get(userId='me', id=mensagem_id, format='full').execute()
            snippet = msg.get('snippet', '')
            return snippet
        except Exception as e:
            return f"Erro ao ler e-mail {mensagem_id}: {str(e)}"

    def enviar_email(self, to: str, assunto: str, corpo: str, anexo_caminho: str = None):
        if not self.service:
            init_msg = self._init_service()
            if "Erro" in init_msg:
                return init_msg
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import base64
            import mimetypes
            
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = assunto
            
            message.attach(MIMEText(corpo, 'plain', 'utf-8'))
            
            if anexo_caminho and os.path.exists(anexo_caminho):
                content_type, encoding = mimetypes.guess_type(anexo_caminho)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                main_type, sub_type = content_type.split('/', 1)
                
                with open(anexo_caminho, 'rb') as f:
                    mime_base = MIMEBase(main_type, sub_type)
                    mime_base.set_payload(f.read())
                    encoders.encode_base64(mime_base)
                    nome_ficheiro = os.path.basename(anexo_caminho)
                    mime_base.add_header('Content-Disposition', f'attachment; filename="{nome_ficheiro}"')
                    message.attach(mime_base)
            elif anexo_caminho:
                return f"Aviso: O ficheiro anexo '{anexo_caminho}' não foi encontrado. E-mail não enviado."

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            self.service.users().messages().send(userId='me', body={'raw': raw}).execute()
            
            msg_sucesso = f"E-mail enviado com sucesso para {to} com o assunto: {assunto}."
            if anexo_caminho:
                msg_sucesso += f" Anexo '{os.path.basename(anexo_caminho)}' incluído."
            return msg_sucesso
        except Exception as e:
            return f"Erro ao enviar e-mail: {str(e)}"
