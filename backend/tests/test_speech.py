from ai.agents.game_designer_agent import GameDesignerAgent
from ai.agents.tutor_agent import TutorAgent
from speech.synthesis import synthesize_speech
from speech.recognition import recognize_speech
import unittest
import pytest
import sys
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))


class TestSpeechFunctions(unittest.TestCase):

    def test_recognize_speech_valid_input(self):
        test_audio_file = 'path/to/test/audio.wav'
        expected_output = 'Hello'
        result = recognize_speech(test_audio_file)
        self.assertEqual(result, expected_output)

    def test_recognize_speech_invalid_input(self):
        test_audio_file = 'path/to/invalid/audio.wav'
        result = recognize_speech(test_audio_file)
        self.assertIsNone(result)

    def test_synthesize_speech(self):
        text_input = 'Hello'
        expected_audio_file = 'path/to/expected/audio.wav'
        result = synthesize_speech(text_input)
        # Assuming the function returns True on success
        self.assertTrue(result)


def test_google_search_integration():
    """Testa a integração com a API de pesquisa do Google"""
    print("\nTestando integração com Google Search API:")

    try:
        # Inicializar os agentes necessários
        game_designer = GameDesignerAgent()
        tutor = TutorAgent(game_designer)

        # Realizar uma pesquisa de teste
        search_query = "exercícios de terapia da fala português"
        results = tutor._search_internet(search_query, max_results=2)

        # Verificar se a pesquisa foi bem sucedida
        assert "success" in results, "Resposta da API não contém campo 'success'"
        assert results.get("success") == True, "Pesquisa falhou"
        assert "results" in results, "Resposta não contém resultados"
        assert len(results["results"]) > 0, "Nenhum resultado encontrado"

        # Verificar estrutura dos resultados
        first_result = results["results"][0]
        assert "title" in first_result, "Resultado não contém título"
        assert "link" in first_result, "Resultado não contém link"
        assert "snippet" in first_result, "Resultado não contém snippet"

        print("✅ Teste de pesquisa realizado com sucesso!")
        print(f"Encontrados {len(results['results'])} resultados")
        print(f"Primeiro resultado: {first_result['title']}\n")

        return True

    except Exception as e:
        print(f"❌ Erro no teste de pesquisa: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    unittest.main()
    test_google_search_integration()
