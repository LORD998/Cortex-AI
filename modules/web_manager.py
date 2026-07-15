from duckduckgo_search import DDGS

class WebManager:
    def __init__(self):
        pass

    def pesquisar_internet(self, pesquisa: str, limite: int = 3):
        """Pesquisa na internet usando DuckDuckGo e devolve um resumo dos resultados."""
        try:
            print(f"[WebManager] A pesquisar no Google/DuckDuckGo: {pesquisa}")
            resultados_texto = []
            
            with DDGS() as ddgs:
                resultados = list(ddgs.text(pesquisa, max_results=limite))
                
                if not resultados:
                    return f"A pesquisa por '{pesquisa}' não devolveu resultados."
                    
                for idx, res in enumerate(resultados):
                    titulo = res.get('title', 'Sem título')
                    resumo = res.get('body', 'Sem descrição')
                    url = res.get('href', '')
                    
                    resultados_texto.append(f"Resultado {idx+1}:\nTítulo: {titulo}\nResumo: {resumo}\nLink: {url}\n")
                    
            return "Pesquisa concluída. Resultados:\n\n" + "\n".join(resultados_texto)
        except Exception as e:
            return f"Erro a pesquisar na internet: {str(e)}"

    def procurar_empregos(self, cargo: str, localizacao: str = "Portugal", limite: int = 5):
        """Procura vagas de emprego usando palavras-chave otimizadas no DuckDuckGo."""
        try:
            pesquisa = f"vagas emprego {cargo} {localizacao} (linkedin OR net-empregos OR itjobs OR indeed)"
            print(f"[WebManager] A procurar empregos: {pesquisa}")
            resultados_texto = []
            
            with DDGS() as ddgs:
                resultados = list(ddgs.text(pesquisa, max_results=limite))
                
                if not resultados:
                    return f"Infelizmente não encontrei vagas recentes para '{cargo}' em '{localizacao}' neste momento."
                    
                for idx, res in enumerate(resultados):
                    titulo = res.get('title', 'Vaga sem título')
                    resumo = res.get('body', 'Sem descrição da vaga')
                    url = res.get('href', '')
                    
                    resultados_texto.append(f"Vaga {idx+1}:\nCargo/Título: {titulo}\nDescrição Breve: {resumo}\nLink da Vaga: {url}\n")
                    
            return f"Encontrei as seguintes vagas para '{cargo}' em '{localizacao}':\n\n" + "\n".join(resultados_texto)
        except Exception as e:
            return f"Erro ao procurar vagas de emprego: {str(e)}"
