"""
Ferramentas específicas para o Game Designer Agent.

Este módulo define ferramentas que permitem ao Game Designer Agent criar
e gerenciar jogos de terapia da fala, incluindo minigames, níveis de dificuldade,
e progressão do jogador.
"""

from typing import Dict, List, Any, Optional, Union
import json
import random
import logging
from pathlib import Path

from .tools import tool_registry
from .speech_tools import WORD_THEMES, WORD_DATABASE, buscar_palavras_com_som, buscar_palavras_por_tema

# Configuração do logger
logger = logging.getLogger("GameTools")

# Tipos de minijogos disponíveis e suas descrições
MINIGAME_TYPES = {
    "encontrar_par": {
        "description": "Encontrar pares de cartões com palavras que contenham o mesmo som",
        "difficulty_levels": 3,
        "min_age": 4
    },
    "completar_palavra": {
        "description": "Completar palavras com sílabas ou letras faltantes",
        "difficulty_levels": 3,
        "min_age": 5
    },
    "ordenar_sequencia": {
        "description": "Ordenar uma sequência de imagens para formar uma história ou processo",
        "difficulty_levels": 3,
        "min_age": 6
    },
    "repeticao_sonora": {
        "description": "Repetir sons ou palavras apresentadas",
        "difficulty_levels": 3,
        "min_age": 3
    },
    "categorizar_palavras": {
        "description": "Classificar palavras em categorias específicas",
        "difficulty_levels": 3,
        "min_age": 5
    },
    "rima_palavras": {
        "description": "Encontrar palavras que rimem com uma palavra dada",
        "difficulty_levels": 3,
        "min_age": 6
    },
    "historia_interativa": {
        "description": "Participar de uma história interativa pronunciando palavras específicas",
        "difficulty_levels": 3,
        "min_age": 4
    },
    "labirinto_sonoro": {
        "description": "Navegar por um labirinto seguindo instruções baseadas em sons",
        "difficulty_levels": 3,
        "min_age": 5
    },
    "palavra_escondida": {
        "description": "Descobrir uma palavra escondida com base em dicas sonoras",
        "difficulty_levels": 3,
        "min_age": 5
    },
    "construtor_frases": {
        "description": "Construir frases usando palavras com sons específicos",
        "difficulty_levels": 3,
        "min_age": 6
    }
}

# Templates para diferentes tipos de atividades
GAME_TEMPLATES = {
    "encontrar_par": {
        "title": "Encontre os Pares de {som}",
        "description": "Encontre os pares de cartões que têm palavras com o som '{som}'.",
        "instructions": "Clique em dois cartões para virá-los. Se eles formarem um par com o som '{som}', você ganha pontos!",
        "template": {
            "type": "memory_game",
            "target_sound": "{som}",
            "cards": [],
            "time_limit": 120,  # segundos
            "score_per_match": 10
        }
    },
    "completar_palavra": {
        "title": "Complete as Palavras com {som}",
        "description": "Complete as palavras adicionando as partes que contêm o som '{som}'.",
        "instructions": "Arraste as sílabas corretas para completar cada palavra.",
        "template": {
            "type": "word_completion",
            "target_sound": "{som}",
            "words": [],
            "missing_parts": [],
            "time_limit": 180,  # segundos
            "score_per_word": 15
        }
    },
    "repeticao_sonora": {
        "title": "Repita o Som {som}",
        "description": "Escute e repita as palavras que contêm o som '{som}'.",
        "instructions": "Clique no botão de áudio para ouvir a palavra, depois clique em 'Gravar' e repita a palavra em voz alta.",
        "template": {
            "type": "repeat_word",
            "target_sound": "{som}",
            "words": [],
            "attempts_allowed": 3,
            "score_per_correct": 20
        }
    }
}


@tool_registry.register(
    name="criar_minijogo",
    description="Cria um minijogo específico para trabalhar um som",
    required_params=["tipo_jogo", "som_alvo"],
    optional_params={"dificuldade": "médio", "tema": None, "idade_paciente": 6}
)
def criar_minijogo(tipo_jogo, som_alvo, dificuldade="médio", tema=None, idade_paciente=6):
    """
    Cria um minijogo para terapia da fala baseado nos parâmetros fornecidos.

    Args:
        tipo_jogo: O tipo de minijogo (ex: "encontrar_par", "completar_palavra")
        som_alvo: O som a ser trabalhado no jogo (ex: "r", "s", "lh")
        dificuldade: Nível de dificuldade ("iniciante", "médio", "avançado")
        tema: Opcional, tema para as palavras (ex: "animais", "alimentos")
        idade_paciente: Idade do paciente, para ajuste de dificuldade

    Returns:
        Um objeto representando o minijogo criado
    """
    logger.info(
        f"Criando minijogo do tipo '{tipo_jogo}' para som '{som_alvo}', dificuldade '{dificuldade}'")

    # Verificar se o tipo de jogo é válido
    if tipo_jogo not in MINIGAME_TYPES:
        tipos_disponiveis = list(MINIGAME_TYPES.keys())
        logger.warning(
            f"Tipo de jogo '{tipo_jogo}' não encontrado. Tipos disponíveis: {tipos_disponiveis}")
        return {
            "erro": f"Tipo de jogo '{tipo_jogo}' não encontrado",
            "tipos_disponiveis": tipos_disponiveis
        }

    # Verificar idade mínima recomendada para o jogo
    idade_minima = MINIGAME_TYPES[tipo_jogo]["min_age"]
    if idade_paciente < idade_minima:
        logger.warning(
            f"Jogo '{tipo_jogo}' recomendado para idade {idade_minima}+, mas paciente tem {idade_paciente}")

    # Obter template do jogo
    game_template = GAME_TEMPLATES.get(tipo_jogo)
    if not game_template:
        # Se não houver um template específico, criar um genérico
        game_template = {
            "title": f"Jogo de {tipo_jogo.replace('_', ' ')} com som {som_alvo}",
            "description": f"Um jogo para praticar o som '{som_alvo}'",
            "instructions": f"Siga as instruções na tela para praticar o som '{som_alvo}'",
            "template": {
                "type": tipo_jogo,
                "target_sound": som_alvo
            }
        }

    # Buscar palavras apropriadas
    quantidade_palavras = 6 if dificuldade == "iniciante" else (
        8 if dificuldade == "médio" else 10)

    if tema:
        # Buscar palavras por tema e som
        palavras_result = buscar_palavras_por_tema(
            tema=tema,
            dificuldade=dificuldade,
            quantidade=quantidade_palavras,
            com_som=som_alvo
        )
        palavras = palavras_result.get("palavras", [])

        # Se não encontrarmos palavras suficientes com o tema e som, buscar só pelo som
        if len(palavras) < quantidade_palavras / 2:
            palavras_result = buscar_palavras_com_som(
                som=som_alvo,
                dificuldade=dificuldade,
                quantidade=quantidade_palavras
            )
            palavras = palavras_result.get("palavras", [])
    else:
        # Buscar palavras apenas pelo som
        palavras_result = buscar_palavras_com_som(
            som=som_alvo,
            dificuldade=dificuldade,
            quantidade=quantidade_palavras
        )
        palavras = palavras_result.get("palavras", [])

    # Criar jogo com base no tipo
    jogo = {
        "id": f"{tipo_jogo}_{som_alvo}_{random.randint(1000, 9999)}",
        "title": game_template["title"].format(som=som_alvo),
        "description": game_template["description"].format(som=som_alvo),
        "instructions": game_template["instructions"].format(som=som_alvo),
        "difficulty": dificuldade,
        "targetSound": som_alvo,
        "theme": tema if tema else "geral",
        "words": palavras,
        "minAgeRecommended": idade_minima,
        "gameConfig": {}
    }

    # Configuração específica para cada tipo de jogo
    if tipo_jogo == "encontrar_par":
        pares = []
        for i in range(min(len(palavras), quantidade_palavras // 2)):
            pares.extend([palavras[i], palavras[i]])

        # Embaralhar os pares
        random.shuffle(pares)

        jogo["gameConfig"] = {
            "type": "memory_game",
            "cards": pares,
            "timeLimit": 60 if dificuldade == "iniciante" else (90 if dificuldade == "médio" else 120),
            "scorePerMatch": 10
        }

    elif tipo_jogo == "completar_palavra":
        # Para cada palavra, determinar que parte contém o som alvo
        palavras_config = []
        for palavra in palavras[:quantidade_palavras]:
            # Dividir a palavra em sílabas (simplificado)
            silabas = []
            for i in range(0, len(palavra), 2):
                if i + 2 <= len(palavra):
                    silabas.append(palavra[i:i+2])
                else:
                    silabas.append(palavra[i:])

            # Determinar qual sílaba contém o som alvo
            silaba_alvo = next(
                (s for s in silabas if som_alvo in s), silabas[0])
            silaba_index = silabas.index(silaba_alvo)

            # Criar configuração para esta palavra
            palavra_config = {
                "word": palavra,
                "syllables": silabas,
                "missingIndex": silaba_index
            }
            palavras_config.append(palavra_config)

        jogo["gameConfig"] = {
            "type": "word_completion",
            "words": palavras_config,
            "timeLimit": 120 if dificuldade == "iniciante" else (180 if dificuldade == "médio" else 240),
            "scorePerWord": 15
        }

    elif tipo_jogo == "repeticao_sonora":
        jogo["gameConfig"] = {
            "type": "repeat_word",
            "words": palavras[:quantidade_palavras],
            "attemptsAllowed": 3,
            "scorePerCorrect": 20,
            "pronunciationThreshold": 0.7 if dificuldade == "iniciante" else (0.8 if dificuldade == "médio" else 0.9)
        }

    else:
        # Configuração genérica para outros tipos de jogos
        jogo["gameConfig"] = {
            "type": tipo_jogo,
            "words": palavras[:quantidade_palavras],
            "difficulty": dificuldade,
            "targetSound": som_alvo
        }

    return jogo


@tool_registry.register(
    name="gerar_sequencia_jogos",
    description="Gera uma sequência de jogos para uma sessão de terapia",
    required_params=["sons_alvo"],
    optional_params={"duracao_minutos": 20,
                     "idade_paciente": 6, "nivel": "médio", "tema": None}
)
def gerar_sequencia_jogos(sons_alvo, duracao_minutos=20, idade_paciente=6, nivel="médio", tema=None):
    """
    Gera uma sequência de minijogos para uma sessão de terapia.

    Args:
        sons_alvo: Lista de sons a serem trabalhados (ex: ["r", "s", "lh"])
        duracao_minutos: Duração aproximada da sessão em minutos
        idade_paciente: Idade do paciente
        nivel: Nível de dificuldade geral ("iniciante", "médio", "avançado")
        tema: Opcional, tema para os jogos

    Returns:
        Uma lista de minijogos para a sessão
    """
    logger.info(
        f"Gerando sequência de jogos para sons {sons_alvo}, duração {duracao_minutos}min, nível {nivel}")

    # Converter para lista se for string
    if isinstance(sons_alvo, str):
        sons_alvo = [s.strip() for s in sons_alvo.split(",")]

    # Estimar quantos jogos cabem na duração
    # Assumindo que cada jogo leva aproximadamente 5 minutos
    num_jogos = max(1, round(duracao_minutos / 5))

    # Tipos de jogos adequados para a idade do paciente
    jogos_por_idade = [tipo for tipo, info in MINIGAME_TYPES.items(
    ) if info["min_age"] <= idade_paciente]

    # Se não houver jogos adequados para a idade, usar todos
    if not jogos_por_idade:
        jogos_por_idade = list(MINIGAME_TYPES.keys())

    # Criar sequência de jogos
    sequencia = []
    for i in range(num_jogos):
        # Selecionar som alvo para este jogo (ciclar pelos sons disponíveis)
        som_index = i % len(sons_alvo)
        som = sons_alvo[som_index]

        # Selecionar tipo de jogo (evitar repetição consecutiva)
        tipos_disponiveis = [t for t in jogos_por_idade if not (
            sequencia and t == sequencia[-1]["type"])]
        if not tipos_disponiveis:
            tipos_disponiveis = jogos_por_idade

        tipo_jogo = random.choice(tipos_disponiveis)

        # Criar o minijogo
        jogo = criar_minijogo(tipo_jogo, som, nivel, tema, idade_paciente)

        # Adicionar à sequência se não houve erro
        if "erro" not in jogo:
            sequencia.append({
                "type": tipo_jogo,
                "sound": som,
                "game": jogo
            })

    return {
        "session": {
            "title": f"Sessão de terapia: Sons {', '.join(sons_alvo)}",
            "duration": duracao_minutos,
            "difficulty": nivel,
            "theme": tema if tema else "variado",
            "targetSounds": sons_alvo,
            "patientAge": idade_paciente,
            "gameCount": len(sequencia),
            "games": sequencia
        }
    }


@tool_registry.register(
    name="avaliar_progresso_jogador",
    description="Avalia o progresso do jogador com base em resultados de jogos anteriores",
    required_params=["historico_jogos"],
    optional_params={"sons_foco": None}
)
def avaliar_progresso_jogador(historico_jogos, sons_foco=None):
    """
    Avalia o progresso do jogador com base nos resultados de jogos anteriores.

    Args:
        historico_jogos: Lista de objetos com resultados de jogos anteriores
        sons_foco: Opcional, sons específicos para focar na análise

    Returns:
        Análise do progresso e recomendações para próximos jogos
    """
    logger.info("Avaliando progresso do jogador com base no histórico de jogos")

    # Converter para lista se não estiver no formato adequado
    if isinstance(historico_jogos, str):
        try:
            historico_jogos = json.loads(historico_jogos)
        except json.JSONDecodeError:
            logger.error("Formato de histórico de jogos inválido")
            return {"erro": "Formato de histórico de jogos inválido"}

    # Se histórico estiver vazio, retornar mensagem
    if not historico_jogos or len(historico_jogos) == 0:
        return {
            "message": "Histórico de jogos vazio. Não é possível avaliar progresso.",
            "recommendations": ["Iniciar com jogos de nível iniciante para fazer uma avaliação inicial."]
        }

    # Converter para lista se sons_foco for string
    if isinstance(sons_foco, str) and sons_foco:
        sons_foco = [s.strip() for s in sons_foco.split(",")]

    # Analisar progresso por som
    progresso_por_som = {}
    jogos_recentes = {}
    nivel_atual = {}

    # Processar cada jogo no histórico
    for jogo in historico_jogos:
        # Extrair informações do jogo
        som = jogo.get("targetSound")
        pontuacao = jogo.get("score", 0)
        pontuacao_maxima = jogo.get("maxScore", 100)
        data = jogo.get("date", "desconhecida")
        nivel = jogo.get("difficulty", "médio")

        # Se não há som definido, pular
        if not som:
            continue

        # Filtrar por sons de foco, se especificados
        if sons_foco and som not in sons_foco:
            continue

        # Inicializar dicionário para este som se não existir
        if som not in progresso_por_som:
            progresso_por_som[som] = {
                "jogos": [],
                "pontuacao_media": 0,
                "progresso": 0  # 0 a 100
            }

        # Adicionar resultado deste jogo
        resultado_percentual = (pontuacao / pontuacao_maxima) * \
            100 if pontuacao_maxima > 0 else 0

        progresso_por_som[som]["jogos"].append({
            "data": data,
            "pontuacao": pontuacao,
            "pontuacao_maxima": pontuacao_maxima,
            "resultado_percentual": resultado_percentual,
            "nivel": nivel
        })

        # Atualizar jogo mais recente para este som
        if som not in jogos_recentes or data > jogos_recentes[som]["data"]:
            jogos_recentes[som] = {
                "data": data,
                "resultado": resultado_percentual,
                "nivel": nivel
            }
            nivel_atual[som] = nivel

    # Calcular métricas por som
    for som, dados in progresso_por_som.items():
        # Ordenar jogos por data (assumindo que a chave 'data' é comparável)
        dados["jogos"].sort(key=lambda x: x["data"])

        # Calcular pontuação média
        total_pontuacao = sum(jogo["resultado_percentual"]
                              for jogo in dados["jogos"])
        dados["pontuacao_media"] = total_pontuacao / \
            len(dados["jogos"]) if dados["jogos"] else 0

        # Calcular tendência de progresso
        if len(dados["jogos"]) >= 2:
            primeiro = dados["jogos"][0]["resultado_percentual"]
            ultimo = dados["jogos"][-1]["resultado_percentual"]
            dados["tendencia"] = ultimo - primeiro

            # Tendência agrupada pelos últimos 3 jogos vs primeiros 3
            if len(dados["jogos"]) >= 6:
                primeiros_3 = sum(jogo["resultado_percentual"]
                                  for jogo in dados["jogos"][:3]) / 3
                ultimos_3 = sum(jogo["resultado_percentual"]
                                for jogo in dados["jogos"][-3:]) / 3
                dados["tendencia_agrupada"] = ultimos_3 - primeiros_3
            else:
                dados["tendencia_agrupada"] = dados["tendencia"]
        else:
            dados["tendencia"] = 0
            dados["tendencia_agrupada"] = 0

        # Determinar nível de progresso (0-100)
        # Baseado na média recente e na tendência
        media_recente = sum(jogo["resultado_percentual"]
                            for jogo in dados["jogos"][-3:]) / min(3, len(dados["jogos"]))
        dados["progresso"] = min(
            100, max(0, media_recente + dados["tendencia_agrupada"] / 5))

    # Gerar recomendações
    recomendacoes = []
    niveis_recomendados = {}

    for som, dados in progresso_por_som.items():
        nivel_recomendado = nivel_atual.get(som, "médio")

        # Ajustar nível com base no progresso
        if dados["progresso"] >= 80 and nivel_recomendado != "avançado":
            nivel_recomendado = "avançado"
            recomendacoes.append(
                f"Aumentar para nível avançado nos exercícios com o som '{som}'")
        elif dados["progresso"] >= 60 and nivel_recomendado == "iniciante":
            nivel_recomendado = "médio"
            recomendacoes.append(
                f"Aumentar para nível médio nos exercícios com o som '{som}'")
        elif dados["progresso"] < 40 and nivel_recomendado != "iniciante":
            nivel_recomendado = "iniciante"
            recomendacoes.append(
                f"Reduzir para nível iniciante nos exercícios com o som '{som}'")

        niveis_recomendados[som] = nivel_recomendado

        # Verificar tendência
        if dados["tendencia"] <= -10:
            recomendacoes.append(
                f"Atenção: Tendência de queda no desempenho com o som '{som}'. Recomenda-se revisão.")

    # Recomendações gerais
    if not recomendacoes:
        recomendacoes.append(
            "Manter o nível atual dos exercícios e continuar o acompanhamento.")

    # Formatar resultado final
    resultado = {
        "summary": {
            "sounds_analyzed": list(progresso_por_som.keys()),
            "total_games": sum(len(dados["jogos"]) for dados in progresso_por_som.values()),
            "average_progress": sum(dados["progresso"] for dados in progresso_por_som.values()) / len(progresso_por_som) if progresso_por_som else 0
        },
        "progress_by_sound": {som: {
            "average_score": round(dados["pontuacao_media"], 1),
            "trend": round(dados["tendencia"], 1),
            "progress_level": round(dados["progresso"], 1),
            "current_level": nivel_atual.get(som, "médio"),
            "recommended_level": niveis_recomendados.get(som, "médio")
        } for som, dados in progresso_por_som.items()},
        "recommendations": recomendacoes
    }

    return resultado


@tool_registry.register(
    name="sugerir_jogos_adaptados",
    description="Sugere jogos adaptados para o nível atual do jogador",
    required_params=["sons_trabalhados", "nivel_atual"],
    optional_params={"idade": 6, "tema_preferido": None, "duracao_sessao": 20}
)
def sugerir_jogos_adaptados(sons_trabalhados, nivel_atual, idade=6, tema_preferido=None, duracao_sessao=20):
    """
    Sugere jogos adaptados para o nível atual do jogador.

    Args:
        sons_trabalhados: Lista de sons a serem trabalhados e seus níveis
        nivel_atual: Nível atual do jogador por som ou geral
        idade: Idade do jogador
        tema_preferido: Tema preferido para os jogos, se houver
        duracao_sessao: Duração da sessão em minutos

    Returns:
        Lista de jogos sugeridos adaptados ao nível do jogador
    """
    logger.info(
        f"Gerando sugestões de jogos adaptados para nível {nivel_atual}")

    # Processar sons e níveis
    if isinstance(sons_trabalhados, dict):
        # Se já vier como dicionário som: nível
        sons_niveis = sons_trabalhados
    elif isinstance(sons_trabalhados, list):
        # Se for uma lista simples de sons, usar o nível geral para todos
        sons_niveis = {som: nivel_atual for som in sons_trabalhados}
    elif isinstance(sons_trabalhados, str):
        # Se for uma string, tentar converter para lista
        sons = [s.strip() for s in sons_trabalhados.split(",")]
        sons_niveis = {som: nivel_atual for som in sons}
    else:
        logger.error(
            f"Formato inválido para sons_trabalhados: {type(sons_trabalhados)}")
        return {"erro": f"Formato inválido para sons_trabalhados: {type(sons_trabalhados)}"}

    # Normalizar nível atual se for string
    if isinstance(nivel_atual, str):
        nivel_default = nivel_atual
        # Converter cada som para usar o nível específico, se disponível no dicionário
        sons_niveis = {som: sons_niveis.get(
            som, nivel_default) for som in sons_niveis.keys()}

    # Gerar sequência de jogos adaptada para cada som
    resultado = {
        "session_plan": {
            "title": "Plano de Sessão Personalizado",
            "duration": duracao_sessao,
            "sounds": list(sons_niveis.keys()),
            "theme": tema_preferido if tema_preferido else "variado"
        },
        "suggested_games": []
    }

    # Distribuir o tempo da sessão entre os sons
    tempo_por_som = duracao_sessao / \
        len(sons_niveis) if sons_niveis else duracao_sessao

    for som, nivel in sons_niveis.items():
        # Gerar sequência para este som
        sequencia = gerar_sequencia_jogos(
            sons_alvo=[som],
            duracao_minutos=tempo_por_som,
            idade_paciente=idade,
            nivel=nivel,
            tema=tema_preferido
        )

        # Adicionar jogos à sugestão
        if "session" in sequencia and "games" in sequencia["session"]:
            for jogo in sequencia["session"]["games"]:
                resultado["suggested_games"].append(jogo)

    # Adicionar variação para sessão
    tipos_usados = [jogo["type"] for jogo in resultado["suggested_games"]]

    # Se há muita repetição de tipo de jogo, tentar adicionar variação
    if len(tipos_usados) > len(set(tipos_usados)) + 1:
        # Encontrar tipos menos usados
        contador_tipos = {}
        for tipo in tipos_usados:
            contador_tipos[tipo] = contador_tipos.get(tipo, 0) + 1

        # Tipos menos usados
        tipos_menos_usados = sorted(
            contador_tipos.keys(), key=lambda k: contador_tipos[k])

        # Sugerir variação
        if tipos_menos_usados:
            resultado[
                "variation_suggestion"] = f"Considerar incluir mais jogos do tipo: {', '.join(tipos_menos_usados[:2])}"

    # Incluir estatísticas da sessão
    resultado["session_plan"]["game_count"] = len(resultado["suggested_games"])
    resultado["session_plan"]["sounds_covered"] = list(sons_niveis.keys())
    resultado["session_plan"]["difficulty_levels"] = sons_niveis

    return resultado


# Exportar todas as funções disponíveis
__all__ = [
    "criar_minijogo",
    "gerar_sequencia_jogos",
    "avaliar_progresso_jogador",
    "sugerir_jogos_adaptados"
]
