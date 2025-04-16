from ai.agents.game_designer_agent import GameDesignerAgent
from ai.agents.tutor_agent import TutorAgent
import sys
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))


def test_google_search():
    """Testa a integração com a API de pesquisa do Google"""
    print("\nTestando integração com Google Search API:")

    try:
        # Inicializar os agentes necessários
        game_designer = GameDesignerAgent()
        tutor = TutorAgent(game_designer)

        # Realizar uma pesquisa de teste
        search_query = "exercícios de terapia da fala português"
        results = tutor._search_internet(search_query, max_results=2)

        print("\nResultados da pesquisa:")
        if "error" in results:
            print(f"❌ Erro: {results['error']}")
            return False

        if results.get("success"):
            print("✅ Pesquisa realizada com sucesso!")
            for i, result in enumerate(results["results"], 1):
                print(f"\nResultado {i}:")
                print(f"Título: {result['title']}")
                print(f"Link: {result['link']}")
                print(f"Descrição: {result['snippet'][:200]}...")
            return True

    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_google_search()
