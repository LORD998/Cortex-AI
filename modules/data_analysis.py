import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path

class DataAnalysis:
    """Módulo para análise de dados (limpeza, merge, gráficos, relatórios)."""
    def __init__(self):
        pass

    def limpar_tabela(self, caminho_csv: str, colunas_remover: list = None):
        """Carrega CSV, remove colunas opcionais e devolve JSON da tabela limpa."""
        try:
            df = pd.read_csv(caminho_csv)
            if colunas_remover:
                df = df.drop(columns=colunas_remover, errors='ignore')
            return df.to_json(orient='records', force_ascii=False)
        except Exception as e:
            return f"Erro ao limpar tabela: {str(e)}"

    def unir_tabelas(self, caminho_csv1: str, caminho_csv2: str, chave: str, tipo: str = 'inner'):
        """Une duas tabelas CSV por chave usando pandas.merge."""
        try:
            df1 = pd.read_csv(caminho_csv1)
            df2 = pd.read_csv(caminho_csv2)
            merged = pd.merge(df1, df2, on=chave, how=tipo)
            return merged.to_json(orient='records', force_ascii=False)
        except Exception as e:
            return f"Erro ao unir tabelas: {str(e)}"

    def gerar_grafico(self, caminho_csv: str, coluna_x: str, coluna_y: str, tipo: str = 'line', output_path: str = None):
        """Gera um gráfico (line, bar, scatter) a partir de CSV e salva como PNG (se output_path)."""
        try:
            df = pd.read_csv(caminho_csv)
            plt.figure(figsize=(8,5))
            if tipo == 'line':
                sns.lineplot(data=df, x=coluna_x, y=coluna_y)
            elif tipo == 'bar':
                sns.barplot(data=df, x=coluna_x, y=coluna_y)
            elif tipo == 'scatter':
                sns.scatterplot(data=df, x=coluna_x, y=coluna_y)
            else:
                return f"Tipo de gráfico '{tipo}' não suportado."
            plt.title(f"{tipo.title()} de {coluna_y} vs {coluna_x}")
            if output_path:
                plt.savefig(output_path, dpi=150)
                return f"Gráfico salvo em {output_path}."
            else:
                return "Gráfico gerado (não salvo)."
        except Exception as e:
            return f"Erro ao gerar gráfico: {str(e)}"

    def calcular_estatisticas(self, caminho_csv: str, colunas: list = None):
        """Calcula estatísticas descritivas (mean, median, std) para colunas selecionadas."""
        try:
            df = pd.read_csv(caminho_csv)
            if colunas:
                df = df[colunas]
            stats = df.describe().to_dict()
            return json.dumps(stats, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao calcular estatísticas: {str(e)}"
