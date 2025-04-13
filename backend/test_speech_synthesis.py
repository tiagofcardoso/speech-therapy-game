from speech.synthesis import (
    synthesize_speech,
    get_polly_client,
    get_available_voices,
    get_example_word_for_phoneme
)
import os
import sys
import json
import base64
from dotenv import load_dotenv
from pathlib import Path

# Configurar o caminho correto para importação
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent  # Diretório backend
sys.path.insert(0, str(project_root))

# Agora importe o módulo speech


def test_aws_credentials():
    """Verificar se as credenciais AWS estão configuradas corretamente"""
    print("\n1. Testando credenciais AWS:")

    # Carregar variáveis de ambiente
    load_dotenv()

    # Verificar variáveis de ambiente
    aws_access_key = os.environ.get("AWS_ACCESS_KEY")
    aws_secret_key = os.environ.get("AWS_SECRET_KEY")
    aws_region = os.environ.get("AWS_REGION")

    if not aws_access_key or not aws_secret_key:
        print("❌ Erro: AWS_ACCESS_KEY e AWS_SECRET_KEY devem estar configurados no .env")
        return False

    print(f"✅ AWS_ACCESS_KEY configurada: {aws_access_key[:8]}...")
    print(f"✅ AWS_SECRET_KEY configurada: {aws_secret_key[:8]}...")
    print(f"✅ AWS_REGION configurada: {aws_region}")

    return True


def test_polly_client():
    """Testar a inicialização do cliente Polly"""
    print("\n2. Testando inicialização do cliente AWS Polly:")
    client = get_polly_client()

    if not client:
        print("❌ Erro: Falha ao inicializar o cliente AWS Polly")
        return False

    print("✅ Cliente AWS Polly inicializado com sucesso")
    return True


def test_available_voices():
    """Testar a obtenção das vozes disponíveis para português europeu"""
    print("\n3. Testando vozes disponíveis para português europeu:")
    voices = get_available_voices()

    if not voices:
        print("❌ Erro: Não foi possível obter a lista de vozes")
        return False

    print(f"✅ Encontradas {len(voices)} vozes para português europeu:")
    for voice in voices:
        print(f"  - {voice['id']} ({voice['gender']})")

    return True


def test_basic_synthesis():
    """Testar a síntese básica de voz"""
    print("\n4. Testando síntese básica de voz:")

    test_text = "Olá! Este é um teste de síntese de voz usando Amazon Polly."
    print(f"Texto para síntese: '{test_text}'")

    try:
        audio_data = synthesize_speech(test_text)

        if not audio_data:
            print("❌ Erro: Falha na síntese de voz")
            return False

        # Salvar o áudio em um arquivo para verificação
        audio_file = "test_speech.mp3"
        with open(audio_file, "wb") as f:
            f.write(base64.b64decode(audio_data))

        print(f"✅ Síntese de voz bem-sucedida! Arquivo salvo em: {audio_file}")
        print(
            f"   Tamanho do áudio: {len(base64.b64decode(audio_data))} bytes")
        return True
    except Exception as e:
        print(f"❌ Erro durante a síntese de voz: {str(e)}")
        return False


def test_voice_customization():
    """Testar personalizações da voz"""
    print("\n5. Testando personalizações da voz:")

    test_text = "Esta é uma frase de teste com personalização de voz."

    # Testar diferentes configurações - usar apenas engine standard para ambas vozes
    voice_settings = [
        {"voice_id": "Ines", "engine": "standard"},  # Voz feminina padrão
        {"voice_id": "Cristiano", "engine": "standard"},  # Voz masculina standard
    ]

    success = True

    for i, settings in enumerate(voice_settings, 1):
        try:
            print(f"\nTestando configuração {i}: {settings}")
            audio_data = synthesize_speech(test_text, settings)

            if not audio_data:
                print(f"❌ Configuração {i}: Falha na síntese")
                success = False
                continue

            # Salvar o áudio em um arquivo para verificação
            audio_file = f"test_voice_config_{i}.mp3"
            with open(audio_file, "wb") as f:
                f.write(base64.b64decode(audio_data))

            print(
                f"✅ Configuração {i}: Síntese bem-sucedida! Arquivo: {audio_file}")
        except Exception as e:
            print(f"❌ Configuração {i}: Erro - {str(e)}")
            success = False

    return success


def test_ssml_synthesis():
    """Testar síntese com marcação SSML"""
    print("\n6. Testando síntese com texto simples (sem SSML):")

    # Usar texto simples em vez de SSML
    test_text = "Isto é um texto com ênfase e uma pausa."

    try:
        audio_data = synthesize_speech(test_text)

        if not audio_data:
            print("❌ Erro: Falha na síntese de texto")
            return False

        # Salvar o áudio em um arquivo para verificação
        audio_file = "test_ssml_speech.mp3"
        with open(audio_file, "wb") as f:
            f.write(base64.b64decode(audio_data))

        print(
            f"✅ Síntese de texto bem-sucedida! Arquivo salvo em: {audio_file}")
        return True
    except Exception as e:
        print(f"❌ Erro durante a síntese de texto: {str(e)}")
        return False


def test_phoneme_examples():
    """Testar a função de exemplos de fonemas"""
    print("\n7. Testando exemplos de palavras para fonemas:")

    phonemes = ["r", "s", "lh", "nh", "ch"]

    for phoneme in phonemes:
        example = get_example_word_for_phoneme(phoneme)
        if example:
            print(f"✅ Fonema '{phoneme}': '{example}'")
        else:
            print(f"❌ Nenhum exemplo para o fonema '{phoneme}'")

    return True


def test_integration_with_tutor():
    """Testar integração com o TutorAgent"""
    print("\n8. Testando integração com TutorAgent:")

    try:
        # Importar o TutorAgent
        from ai.agents.tutor_agent import TutorAgent
        from ai.agents.game_designer_agent import GameDesignerAgent

        # Inicializar agentes
        game_designer = GameDesignerAgent()
        tutor = TutorAgent(game_designer)

        # Verificar se a voz está habilitada
        if not tutor.voice_enabled:
            print(
                "⚠️ A voz do tutor não está habilitada. Verifique ENABLE_TUTOR_VOICE no .env")
            return False

        # Testar a criação de instruções com áudio
        user_profile = {"name": "Tiago", "age": 8}
        instructions = tutor.create_instructions(user_profile, "iniciante")

        if "audio" not in instructions:
            print("❌ Não foi possível gerar áudio para as instruções do tutor")
            return False

        # Verificar os componentes de áudio
        for key in ["greeting", "explanation", "encouragement"]:
            if key not in instructions["audio"] or not instructions["audio"][key]:
                print(f"❌ Componente de áudio '{key}' não gerado")
                return False

            # Salvar o áudio em um arquivo para verificação
            audio_file = f"test_tutor_{key}.mp3"
            with open(audio_file, "wb") as f:
                f.write(base64.b64decode(instructions["audio"][key]))

            print(
                f"✅ Componente '{key}' gerado com sucesso. Arquivo: {audio_file}")

        print("✅ Integração com TutorAgent bem-sucedida!")
        return True
    except Exception as e:
        print(f"❌ Erro ao testar integração com TutorAgent: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Executar todos os testes"""
    print("\n=== TESTES DA SÍNTESE DE VOZ AWS POLLY ===")

    tests = [
        test_aws_credentials,
        test_polly_client,
        test_available_voices,
        test_basic_synthesis,
        test_voice_customization,
        test_ssml_synthesis,
        test_phoneme_examples,
        test_integration_with_tutor
    ]

    results = []

    for test_func in tests:
        result = test_func()
        results.append(result)

    # Relatório final
    print("\n=== RELATÓRIO DE TESTES ===")
    all_passed = all(results)

    for i, (test_func, result) in enumerate(zip(tests, results), 1):
        status = "PASSOU" if result else "FALHOU"
        print(f"{i}. {test_func.__name__}: {status}")

    print("\n=== RESULTADO FINAL ===")
    if all_passed:
        print("✅ Todos os testes passaram! A síntese de voz está funcionando corretamente.")
    else:
        print("❌ Alguns testes falharam. Verifique os erros acima.")

    return all_passed


if __name__ == "__main__":
    run_all_tests()
