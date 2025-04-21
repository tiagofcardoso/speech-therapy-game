import os
import json
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("SearchTool")


class GoogleSearchTool:
    """Ferramenta para realizar buscas usando a Google Search API"""

    def __init__(self, api_key=None):
        """
        Inicializa a ferramenta de busca Google

        Args:
            api_key: Chave da API do Google (opcional, pode ser obtida do ambiente)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Google API KEY é necessária para a ferramenta de busca")

        self.search_engine_id = os.getenv(
            'GOOGLE_SEARCH_ENGINE_ID', '017576662512468239146:omuauf_lfve')
        self.logger = logging.getLogger("GoogleSearchTool")
        self.logger.info("GoogleSearchTool inicializada")

    def search(self, query, num_results=5, language="pt-BR"):
        """
        Realiza uma busca com a Google Search API

        Args:
            query: Consulta a ser pesquisada
            num_results: Número de resultados a retornar (máx. 10)
            language: Código do idioma para resultados

        Returns:
            Lista de resultados da busca
        """
        try:
            self.logger.info(f"Realizando busca por: '{query}'")

            # Garantir que num_results esteja dentro dos limites
            num_results = min(max(1, num_results), 10)

            # Construir URL para a API Google Custom Search
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": num_results,
                "lr": f"lang_{language[:2]}",  # Idioma de busca
                # País para resultados locais
                "gl": language.split("-")[1] if "-" in language else "BR",
                "safe": "active"  # Filtro de conteúdo
            }

            # Fazer a requisição à API
            response = requests.get(url, params=params)
            response.raise_for_status()  # Verificar erros HTTP

            search_results = response.json()

            # Processar e simplificar os resultados
            if "items" in search_results:
                results = []
                for item in search_results["items"]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "google"
                    })
                self.logger.info(
                    f"Busca concluída, retornando {len(results)} resultados")
                return results
            else:
                self.logger.warning("Nenhum resultado encontrado")
                return []

        except Exception as e:
            self.logger.error(f"Erro ao realizar busca: {str(e)}")
            return [{"error": f"Falha na busca: {str(e)}"}]

    def search_therapy_exercise(self, sound, difficulty, age_group="crianças"):
        """
        Busca exercícios específicos de terapia da fala

        Args:
            sound: Som/fonema alvo (ex: "r", "s", "lh")
            difficulty: Nível de dificuldade (iniciante, médio, avançado)
            age_group: Grupo etário (crianças, adultos)

        Returns:
            Informações sobre exercícios relevantes para o som alvo
        """
        # Construir uma consulta específica para terapia da fala
        query = f"exercícios terapia fala fonema {sound} {age_group} nível {difficulty}"

        results = self.search(query, num_results=3)

        # Adicionar uma busca secundária mais específica
        if not results or len(results) < 2:
            secondary_query = f"como pronunciar som {sound} português fonoaudiologia"
            secondary_results = self.search(secondary_query, num_results=2)
            results.extend(secondary_results)

        return results

    def search_personalized_activity(self, interest, sound, difficulty):
        """
        Busca atividades personalizadas baseadas nos interesses do usuário

        Args:
            interest: Interesse específico do usuário (ex: "dinossauros", "futebol")
            sound: Som/fonema alvo
            difficulty: Nível de dificuldade

        Returns:
            Sugestões de atividades relacionadas ao interesse e adequadas para praticar o som
        """
        query = f"atividades {interest} palavras som {sound} terapia fala infantil"

        results = self.search(query, num_results=3)

        # Extrair apenas os snippets mais relevantes
        summaries = [result["snippet"]
                     for result in results if "snippet" in result]

        return {
            "interest": interest,
            "sound": sound,
            "difficulty": difficulty,
            "suggestions": summaries,
            "full_results": results
        }
