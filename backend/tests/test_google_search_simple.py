import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path


def test_google_search():
    """Testa diretamente a API do Google Search"""
    print("\nTestando API do Google Search:")

    # Carregar variáveis de ambiente
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(env_path)

    # Obter credenciais
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        print("❌ Erro: Credenciais não encontradas no arquivo .env")
        return False

    try:
        # Configurar a pesquisa
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': "exercícios de terapia da fala português",
            'num': 2
        }

        # Fazer a requisição
        print("Fazendo requisição para API do Google...")
        response = requests.get(url, params=params)

        # Verificar o status da resposta
        if response.status_code != 200:
            print(f"❌ Erro na API: Status {response.status_code}")
            return False

        # Processar os resultados
        data = response.json()
        if 'items' not in data:
            print("❌ Nenhum resultado encontrado")
            return False

        # Mostrar resultados
        print("\n✅ Pesquisa realizada com sucesso!")
        print(f"Encontrados {len(data['items'])} resultados:")

        for i, item in enumerate(data['items'], 1):
            print(f"\nResultado {i}:")
            print(f"Título: {item['title']}")
            print(f"Link: {item['link']}")
            print(f"Descrição: {item.get('snippet', '')[:200]}...")

        return True

    except Exception as e:
        print(f"❌ Erro ao realizar pesquisa: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_google_search()
