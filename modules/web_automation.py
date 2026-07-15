import subprocess
import os
import json

class WebAutomation:
    """Módulo para automação de navegação web usando Playwright (Chromium)."""
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        # Playwright será instalado sob demanda

    def iniciar_navegador(self):
        """Abre um navegador Chromium headless (ou visível se necessário)."""
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            return "Navegador Chromium iniciado com sucesso."
        except Exception as e:
            return f"Erro ao iniciar navegador: {str(e)}"

    def abrir_url(self, url: str):
        """Navega até a URL especificada."""
        if not self.page:
            self.iniciar_navegador()
        try:
            self.page.goto(url)
            return f"Página carregada: {url}"
        except Exception as e:
            return f"Erro ao abrir URL '{url}': {str(e)}"

    def pesquisar_google(self, termos: str, num_resultados: int = 5):
        """Realiza uma pesquisa no Google e devolve os títulos e links dos resultados."""
        if not self.page:
            self.iniciar_navegador()
        try:
            self.page.goto("https://www.google.com")
            self.page.fill("input[name='q']", termos)
            self.page.press("input[name='q']", "Enter")
            self.page.wait_for_load_state("networkidle")
            resultados = []
            itens = self.page.query_selector_all('div.g')[:num_resultados]
            for i in itens:
                titulo = i.query_selector('h3').inner_text() if i.query_selector('h3') else 'Sem título'
                link = i.query_selector('a').get_attribute('href') if i.query_selector('a') else 'Sem link'
                resultados.append({"titulo": titulo, "link": link})
            return json.dumps(resultados, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao pesquisar no Google: {str(e)}"

    def fechar_navegador(self):
        """Fecha o navegador e liberta recursos."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            return "Navegador fechado."
        except Exception as e:
            return f"Erro ao fechar navegador: {str(e)}"
