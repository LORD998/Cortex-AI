import os
import json
import pandas as pd
from pathlib import Path

class BusinessManager:
    """Módulo de apoio a lojas e negócios (Shopify, CSV, Excel, pricing)."""

    def __init__(self):
        self.shopify_session = None  # será inicializado sob demanda

    # --------------------------- Shopify ---------------------------
    def _init_shopify(self, api_key: str, password: str, shop_name: str):
        try:
            import shopify
            shop_url = f"https://{api_key}:{password}@{shop_name}.myshopify.com/admin"
            shopify.ShopifyResource.set_site(shop_url)
            self.shopify_session = shopify
            return "Sessão Shopify inicializada."
        except Exception as e:
            return f"Erro ao iniciar Shopify: {str(e)}"

    def criar_produto_shopify(self, titulo: str, descricao: str, preco: float, estoque: int, imagens: list = None):
        """Cria um produto na loja Shopify."""
        if not self.shopify_session:
            return "Shopify não está configurado. Chame _init_shopify primeiro."
        try:
            product = self.shopify_session.Product()
            product.title = titulo
            product.body_html = descricao
            product.variants = [{"price": str(preco), "inventory_quantity": estoque}]
            if imagens:
                product.images = [{"src": img} for img in imagens]
            product.save()
            return f"Produto '{titulo}' criado (ID: {product.id})."
        except Exception as e:
            return f"Erro ao criar produto: {str(e)}"

    # --------------------------- CSV/Excel ---------------------------
    def atualizar_csv(self, caminho: str, dados: list, campos: list):
        """Adiciona linhas a um CSV existente ou cria um novo."""
        try:
            df = pd.DataFrame(dados, columns=campos)
            file_path = Path(caminho)
            if file_path.exists():
                df.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8')
            else:
                df.to_csv(file_path, index=False, encoding='utf-8')
            return f"CSV atualizado em {caminho}."
        except Exception as e:
            return f"Erro ao atualizar CSV: {str(e)}"

    def gerar_relatorio_excel(self, dados: list, campos: list, caminho: str):
        """Gera um relatório em Excel a partir de dados tabulares."""
        try:
            df = pd.DataFrame(dados, columns=campos)
            file_path = Path(caminho)
            df.to_excel(file_path, index=False, engine='openpyxl')
            return f"Relatório Excel criado em {caminho}."
        except Exception as e:
            return f"Erro ao gerar Excel: {str(e)}"

    # --------------------------- Preço & Margem ---------------------------
    def calcular_margem(self, custo: float, preco_venda: float):
        """Calcula a margem de lucro percentualmente."""
        try:
            if preco_venda == 0:
                return "Preço de venda não pode ser zero."
            margem = ((preco_venda - custo) / preco_venda) * 100
            return f"Margem: {margem:.2f}%"
        except Exception as e:
            return f"Erro ao calcular margem: {str(e)}"

    # --------------------------- Texto publicitário ---------------------------
    def gerar_descricao_produto(self, nome: str, caracteristicas: list, idioma: str = "pt"):
        """Gera uma descrição de produto a partir de características usando LLM (placeholder)."""
        # Para simplificar, concatenamos as características.
        descricao = f"{nome}: " + ", ".join(caracteristicas) + "."
        return descricao

    # --------------------------- Análise de concorrentes ---------------------------
    def analisar_concorrentes(self, lista_urls: list):
        """Faz download de páginas de concorrentes e extrai preço, avaliação, prazo de entrega (simplificado)."""
        try:
            from bs4 import BeautifulSoup
            import requests
            resultados = []
            for url in lista_urls:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                # Exemplos genéricos – o utilizador pode adaptar selectors.
                preco = soup.select_one('.price')
                avaliacao = soup.select_one('.rating')
                prazo = soup.select_one('.delivery-time')
                resultados.append({
                    "url": url,
                    "preco": preco.text.strip() if preco else "N/A",
                    "avaliacao": avaliacao.text.strip() if avaliacao else "N/A",
                    "prazo": prazo.text.strip() if prazo else "N/A"
                })
            return json.dumps(resultados, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao analisar concorrentes: {str(e)}"
