import time
import threading
from speech.synthesis import synthesize_speech


def performance_test(iterations=50, concurrent=5):
    """Testa a performance da síntese de voz com chamadas concorrentes"""
    print(
        f"\n=== TESTE DE PERFORMANCE: {iterations} iterações, {concurrent} concorrentes ===")

    test_texts = [
        "Olá, isto é um teste de síntese de voz.",
        "Eu gosto de praticar a pronúncia de palavras difíceis.",
        "O rato roeu a roupa do rei de Roma.",
        "A zebra Zizi fez zinco com o zum-zum da abelha.",
        "Três tigres tristes para três pratos de trigo."
    ]

    results = {"success": 0, "errors": 0, "total_time": 0}

    def worker(worker_id):
        for i in range(iterations // concurrent):
            text = test_texts[i % len(test_texts)]
            start_time = time.time()

            try:
                audio_data = synthesize_speech(text)
                if audio_data:
                    results["success"] += 1
                else:
                    results["errors"] += 1
                elapsed = time.time() - start_time
                results["total_time"] += elapsed
                print(
                    f"Worker {worker_id}, Iteração {i+1}: {len(text)} caracteres em {elapsed:.2f}s")
            except Exception as e:
                results["errors"] += 1
                print(f"Worker {worker_id}, Iteração {i+1}: ERRO - {str(e)}")

            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.1)

    threads = []
    start_total = time.time()

    # Iniciar threads de trabalhadores
    for i in range(concurrent):
        t = threading.Thread(target=worker, args=(i+1,))
        threads.append(t)
        t.start()

    # Aguardar todas as threads terminarem
    for t in threads:
        t.join()

    total_elapsed = time.time() - start_total

    # Resultados finais
    print("\n=== RESULTADOS DO TESTE DE PERFORMANCE ===")
    print(f"Total de sínteses: {results['success'] + results['errors']}")
    print(f"Sínteses bem-sucedidas: {results['success']}")
    print(f"Erros: {results['errors']}")
    if results["success"] > 0:
        print(
            f"Tempo médio por síntese: {results['total_time'] / results['success']:.2f}s")
    print(f"Tempo total do teste: {total_elapsed:.2f}s")
    if total_elapsed > 0:
        print(
            f"Taxa de síntese: {(results['success'] + results['errors']) / total_elapsed:.2f} por segundo")


if __name__ == "__main__":
    # Teste com 50 sínteses, 5 concorrentes
    performance_test(iterations=50, concurrent=5)
