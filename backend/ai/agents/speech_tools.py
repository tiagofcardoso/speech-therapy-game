"""
Implementação de ferramentas específicas para terapia da fala.

Este módulo define ferramentas que podem ser usadas pelos agentes para
realizar tarefas relacionadas à terapia da fala, como busca de palavras
com sons específicos, avaliação de pronúncias, etc.
"""
from typing import List, Dict, Any, Optional
import random
import re
import logging
import json
import os
from pathlib import Path

from .tools import tool_registry

# Configuração do logger
logger = logging.getLogger("SpeechTools")

# Base de dados de palavras em português organizadas por som
# Esta é uma versão simplificada. Em produção, seria melhor usar um banco de dados externo
# ou um arquivo JSON mais abrangente.
WORD_DATABASE = {
    # Oclusivas
    "p": ["pato", "pé", "pipoca", "perto", "porta", "pulo", "presente", "papai", "papel", "pipa", "púrpura"],
    "b": ["bola", "bebê", "barco", "boca", "banana", "bonito", "beber", "bravo", "brincar", "brinquedo"],
    "t": ["tatu", "tomada", "telhado", "tia", "tapete", "telefone", "tomate", "tambor", "tigre", "torta"],
    "d": ["dado", "dedo", "dia", "doce", "dança", "dinossauro", "dominó", "desenho", "dormir", "dente"],
    "k": ["casa", "corpo", "cortar", "cama", "cavalo", "caneta", "carro", "coco", "cubo", "capa"],
    "g": ["gato", "galinha", "goiaba", "gelo", "guitarra", "garfo", "gol", "garganta", "goma", "guloso"],

    # Fricativas
    "f": ["faca", "fogo", "feijão", "festa", "foto", "fofoca", "feliz", "folha", "foguete", "família"],
    "v": ["vaca", "vovó", "vida", "vale", "vela", "violão", "vermelho", "vassoura", "vento", "vestido"],
    "s": ["sapo", "sopa", "sino", "sol", "sapato", "suco", "semana", "serra", "sorvete", "sorriso"],
    "z": ["zebra", "zero", "zinco", "zoológico", "zangado", "zigzag", "zumbido", "zona", "zelo", "zíper"],
    "sh": ["chave", "chuva", "chinelo", "chá", "chocolate", "choro", "cheio", "charme", "chique", "cheiro"],
    "j": ["janela", "jogo", "jeito", "jabuti", "joia", "jornal", "jarro", "jacaré", "jipe", "joaninha"],

    # Nasais
    "m": ["mão", "mesa", "meia", "mamãe", "maçã", "mala", "macaco", "medo", "mel", "moto"],
    "n": ["nariz", "navio", "ninho", "nome", "nuvem", "nada", "número", "noite", "novo", "neném"],
    "nh": ["ninho", "sonho", "banho", "linha", "rainha", "carinho", "senhora", "galinha", "minhoca", "espanhol"],

    # Líquidas
    "l": ["lua", "lata", "lobo", "livro", "lápis", "lixo", "limão", "lago", "leite", "leão"],
    "lh": ["palha", "palheta", "coelho", "milho", "toalha", "alho", "velho", "folha", "telha", "olho"],
    "r": ["rato", "rua", "rosa", "rei", "roupa", "raposa", "rede", "riso", "roda", "rio"],
    "rr": ["carro", "terra", "ferro", "serra", "erro", "corrida", "cachorro", "garrafa", "barro", "correr"],

    # Dígrafos e encontros consonantais comuns
    "pr": ["prato", "praia", "preso", "preço", "preto", "primo", "prancha", "prova", "prédio", "privado"],
    "br": ["braço", "brinco", "bravo", "brasa", "brinquedo", "brincadeira", "bruxa", "brilho", "broto", "briga"],
    "tr": ["trato", "trem", "trigo", "troca", "trilho", "trabalho", "trovão", "triste", "trevo", "truque"],
    "dr": ["drama", "droga", "dragão", "drone", "dreno", "drible", "drástico", "dramático", "drogaria", "drenagem"],
    "cr": ["cravo", "creme", "criança", "crocodilo", "cruzeiro", "crista", "crescer", "crença", "criar", "crise"],
    "gr": ["grama", "grito", "grave", "grosso", "graça", "grilo", "grade", "greve", "grupo", "grau"],
    "fr": ["fraco", "frio", "frente", "frango", "frase", "fruta", "frasco", "frade", "freira", "freio"],
    "vr": ["livro", "palavra", "lavrador", "pobre", "livre", "lebre", "obra", "febril", "cobrir", "abrir"],
    "pl": ["placa", "planeta", "pluma", "plano", "planta", "plástico", "plateia", "pleno", "plural", "plebiscito"],
    "bl": ["bloco", "blusa", "blindado", "blasfêmia", "bloqueio", "blefe", "biblioteca", "blindar", "blasé", "blues"],
    "cl": ["classe", "clima", "clipe", "clone", "clube", "clareza", "clave", "cloro", "clínica", "clamor"],
    "gl": ["globo", "glória", "glúten", "glacial", "glicose", "glóbulo", "glutão", "gleba", "gladiador", "glass"],
    "fl": ["flor", "flauta", "flecha", "floco", "flanela", "fluir", "flertar", "fluxo", "flutuação", "flexão"]
}

# Palavras adicionais organizadas por dificuldade para cada nível
# Estas são palavras sem categorização por som específico
WORD_DIFFICULTY = {
    "iniciante": [
        "bola", "casa", "dedo", "faca", "gato", "lua", "mão", "pato", "sapo", "tatu", "vaca", "água", "rato",
        "maçã", "bolo", "pai", "mãe", "céu", "sol", "avó", "mesa", "cama", "leite", "ovo", "doce", "pão",
        "pé", "rio", "mar", "flor", "luz", "cor", "dia", "papai", "suco", "foto", "meia", "fogo", "lobo"
    ],
    "médio": [
        "sapato", "cabelo", "janela", "boneca", "amigo", "escola", "telefone", "cavalo", "camisa", "menino",
        "jardim", "banana", "relógio", "floresta", "vestido", "cidade", "florido", "trabalho", "colorido",
        "cachorro", "passarinho", "sorvete", "professor", "música", "desenho", "estrela", "bolacha", "família",
        "alegria", "viagem", "telhado", "cozinha", "ônibus", "cinema", "quadrado", "abraço", "formiga", "domingo"
    ],
    "avançado": [
        "refrigerante", "computador", "borboleta", "bicicleta", "travesseiro", "alfabeto", "chocolate",
        "elefante", "hipopótamo", "dinossauro", "professora", "dinossauro", "biblioteca", "fotografia",
        "escorregador", "matemática", "paralelepípedo", "helicóptero", "calendário", "geladeira", "supermercado",
        "ambulância", "felicidade", "maravilhoso", "personagem", "informática", "representante", "adolescente",
        "ventilador", "temperatura", "sentimento", "diferente", "girassol", "tartaruga", "participar"
    ]
}

# Categorias temáticas para palavras (útil para jogos)
WORD_THEMES = {
    "animais": ["gato", "cão", "pato", "peixe", "leão", "tigre", "cobra", "urso", "cavalo", "vaca", "rato", "elefante",
                "girafa", "macaco", "zebra", "sapo", "tartaruga", "formiga", "aranha", "abelha", "borboleta", "galinha",
                "pássaro", "coelho", "golfinho", "foca", "baleia", "jacaré", "lobo", "raposa"],

    "alimentos": ["maçã", "banana", "laranja", "uva", "pêra", "morango", "abacaxi", "melancia", "pão", "bolo", "sorvete",
                  "pizza", "sopa", "arroz", "feijão", "ovo", "leite", "queijo", "carne", "frango", "peixe", "batata",
                  "cenoura", "tomate", "alface", "cebola", "chocolate", "biscoito", "suco", "água"],

    "escola": ["lápis", "caneta", "caderno", "livro", "borracha", "régua", "mochila", "professor", "aluno", "classe",
               "quadro", "carteira", "giz", "recreio", "nota", "prova", "tarefa", "estudar", "ler", "escrever", "desenhar",
               "pintar", "aprender", "ensinar", "escola", "biblioteca", "matemática", "história", "ciência", "português"],

    "casa": ["mesa", "cadeira", "sofá", "cama", "travesseiro", "cobertor", "janela", "porta", "telhado", "parede", "cozinha",
             "sala", "quarto", "banheiro", "garagem", "jardim", "escada", "piso", "teto", "luz", "geladeira", "fogão", "pia",
             "chuveiro", "vaso", "cortina", "tapete", "espelho", "quadro", "armário"],

    "corpo": ["cabeça", "olho", "nariz", "boca", "orelha", "cabelo", "braço", "mão", "dedo", "perna", "pé", "barriga", "costas",
              "ombro", "joelho", "cotovelo", "rosto", "pescoço", "dente", "língua", "coração", "pulmão", "cérebro", "osso",
              "pele", "sangue", "músculo", "unha", "queixo", "testa"]
}


@tool_registry.register(
    name="buscar_palavras_com_som",
    description="Busca palavras em português que contêm o som especificado",
    required_params=["som"],
    optional_params={"dificuldade": "médio",
                     "quantidade": 5, "posicao": "qualquer"}
)
def buscar_palavras_com_som(som, dificuldade="médio", quantidade=5, posicao="qualquer"):
    """
    Busca palavras que contêm um som específico.

    Args:
        som: O som a buscar (ex: "p", "r", "lh")
        dificuldade: Nível de dificuldade ("iniciante", "médio", "avançado")
        quantidade: Número de palavras a retornar
        posicao: Posição do som na palavra ("inicio", "meio", "fim", "qualquer")

    Returns:
        Lista de palavras que contêm o som especificado
    """
    logger.info(
        f"Buscando {quantidade} palavras com o som '{som}' (dificuldade: {dificuldade}, posição: {posicao})")

    # Verificar se o som está na nossa base de dados
    if som not in WORD_DATABASE:
        # Tentar encontrar sons similares
        similar_sounds = [s for s in WORD_DATABASE.keys() if som in s]
        if similar_sounds:
            som = similar_sounds[0]
            logger.info(
                f"Som '{som}' não encontrado diretamente. Usando som similar: '{som}'")
        else:
            logger.warning(f"Som '{som}' não encontrado na base de dados")
            # Retornar algumas palavras aleatórias do nível adequado
            if dificuldade in WORD_DIFFICULTY:
                result = random.sample(WORD_DIFFICULTY[dificuldade], min(
                    quantidade, len(WORD_DIFFICULTY[dificuldade])))
                return {"palavras": result, "som": som}
            return {"palavras": [], "som": som, "erro": "Som não encontrado"}

    # Obter palavras para o som
    palavras = WORD_DATABASE.get(som, [])

    # Filtrar por dificuldade
    if dificuldade == "iniciante":
        palavras = [p for p in palavras if len(p) <= 5]
    elif dificuldade == "avançado":
        palavras = [p for p in palavras if len(p) > 6]

    # Filtrar por posição do som na palavra
    if posicao == "inicio":
        palavras = [p for p in palavras if p.startswith(som)]
    elif posicao == "fim":
        palavras = [p for p in palavras if p.endswith(som)]
    elif posicao == "meio":
        palavras = [p for p in palavras if som in p and not p.startswith(
            som) and not p.endswith(som)]

    # Se não tivermos palavras suficientes, complementar com palavras do nível adequado
    if len(palavras) < quantidade and dificuldade in WORD_DIFFICULTY:
        # Filtrar palavras que contêm o som
        additional_words = [
            w for w in WORD_DIFFICULTY[dificuldade] if som in w]
        # Adicionar palavras que ainda não estão na lista
        for word in additional_words:
            if word not in palavras:
                palavras.append(word)
                if len(palavras) >= quantidade:
                    break

    # Embaralhar e limitar à quantidade solicitada
    random.shuffle(palavras)
    result = palavras[:quantidade]

    return {
        "palavras": result,
        "som": som,
        "quantidade": len(result)
    }


@tool_registry.register(
    name="buscar_palavras_por_tema",
    description="Busca palavras em português que pertencem a um tema específico",
    required_params=["tema"],
    optional_params={"dificuldade": "médio", "quantidade": 5, "com_som": None}
)
def buscar_palavras_por_tema(tema, dificuldade="médio", quantidade=5, com_som=None):
    """
    Busca palavras que pertencem a um tema específico.

    Args:
        tema: O tema das palavras (ex: "animais", "alimentos", "escola")
        dificuldade: Nível de dificuldade ("iniciante", "médio", "avançado")
        quantidade: Número de palavras a retornar
        com_som: Opcional, filtrar apenas palavras que contêm este som

    Returns:
        Lista de palavras do tema especificado
    """
    logger.info(
        f"Buscando {quantidade} palavras do tema '{tema}' (dificuldade: {dificuldade})")

    # Verificar se o tema existe
    if tema not in WORD_THEMES:
        # Tentar encontrar temas similares
        similar_themes = [
            t for t in WORD_THEMES.keys() if tema in t or t in tema]
        if similar_themes:
            tema = similar_themes[0]
            logger.info(
                f"Tema '{tema}' não encontrado diretamente. Usando tema similar: '{tema}'")
        else:
            logger.warning(f"Tema '{tema}' não encontrado na base de dados")
            # Retornar algumas palavras aleatórias do nível adequado
            if dificuldade in WORD_DIFFICULTY:
                result = random.sample(WORD_DIFFICULTY[dificuldade], min(
                    quantidade, len(WORD_DIFFICULTY[dificuldade])))
                return {"palavras": result, "tema": "geral"}
            return {"palavras": [], "tema": tema, "erro": "Tema não encontrado"}

    # Obter palavras do tema
    palavras = WORD_THEMES.get(tema, [])

    # Filtrar por dificuldade
    if dificuldade == "iniciante":
        palavras = [p for p in palavras if len(p) <= 5]
    elif dificuldade == "avançado":
        palavras = [p for p in palavras if len(p) > 6]

    # Filtrar por som, se especificado
    if com_som:
        palavras = [p for p in palavras if com_som in p]

    # Se não tivermos palavras suficientes e um som foi especificado, buscar palavras com esse som
    if len(palavras) < quantidade and com_som:
        # Buscar palavras com o som especificado
        sound_result = buscar_palavras_com_som(
            com_som, dificuldade, quantidade=10)
        additional_words = sound_result.get("palavras", [])
        # Adicionar palavras que ainda não estão na lista
        for word in additional_words:
            if word not in palavras:
                palavras.append(word)
                if len(palavras) >= quantidade:
                    break

    # Embaralhar e limitar à quantidade solicitada
    random.shuffle(palavras)
    result = palavras[:quantidade] if len(palavras) >= quantidade else palavras

    return {
        "palavras": result,
        "tema": tema,
        "quantidade": len(result)
    }


@tool_registry.register(
    name="avaliar_dificuldade_palavra",
    description="Avalia a dificuldade de uma palavra para pronúncia em terapia da fala",
    required_params=["palavra"],
    optional_params={}
)
def avaliar_dificuldade_palavra(palavra):
    """
    Avalia a dificuldade de uma palavra para pronúncia.

    Args:
        palavra: A palavra a ser avaliada

    Returns:
        Dicionário com informações sobre a dificuldade da palavra
    """
    logger.info(f"Avaliando dificuldade da palavra: '{palavra}'")

    palavra = palavra.lower().strip()

    # Critérios de avaliação
    tamanho = len(palavra)
    silabas = len(re.findall(r'[aeiouáàâãéêíóôúy]+', palavra, re.IGNORECASE))

    # Detectar encontros consonantais difíceis
    encontros_dificeis = re.findall(
        r'[bcdfghjklmnpqrstvwxyz]{3,}', palavra, re.IGNORECASE)
    tem_encontros_dificeis = len(encontros_dificeis) > 0

    # Detectar sons tipicamente difíceis em português
    sons_dificeis = ["rr", "lh", "nh", "ch", "pr", "tr",
                     "br", "cr", "gr", "pl", "gl", "fl", "dr", "tl"]
    sons_presentes = [som for som in sons_dificeis if som in palavra]

    # Calcular pontuação de dificuldade (0-10)
    pontuacao = 0

    # Tamanho da palavra (até 3 pontos)
    if tamanho <= 3:
        pontuacao += 0
    elif tamanho <= 5:
        pontuacao += 1
    elif tamanho <= 7:
        pontuacao += 2
    else:
        pontuacao += 3

    # Número de sílabas (até 3 pontos)
    pontuacao += min(silabas, 3)

    # Encontros consonantais difíceis (até 2 pontos)
    if tem_encontros_dificeis:
        pontuacao += min(len(encontros_dificeis) * 2, 2)

    # Sons difíceis (até 2 pontos)
    pontuacao += min(len(sons_presentes), 2)

    # Determinar nível de dificuldade
    nivel = "iniciante"
    if pontuacao >= 7:
        nivel = "avançado"
    elif pontuacao >= 4:
        nivel = "médio"

    # Identificar sons presentes na palavra
    todos_sons = {
        som: 1 for som in WORD_DATABASE.keys() if som in palavra
    }

    return {
        "palavra": palavra,
        "dificuldade": {
            "nivel": nivel,
            "pontuacao": pontuacao,
            "tamanho": tamanho,
            "silabas": silabas,
            "encontros_dificeis": encontros_dificeis if tem_encontros_dificeis else [],
            "sons_dificeis": sons_presentes
        },
        "sons": list(todos_sons.keys()) if todos_sons else []
    }


@tool_registry.register(
    name="gerar_dica_visual",
    description="Gera uma dica visual para uma palavra",
    required_params=["palavra"],
    optional_params={"tipo": "descricao"}
)
def gerar_dica_visual(palavra, tipo="descricao"):
    """
    Gera uma dica visual para uma palavra.

    Args:
        palavra: A palavra para a qual gerar uma dica visual
        tipo: O tipo de dica ("descricao", "emoji", "url")

    Returns:
        Uma dica visual para a palavra
    """
    logger.info(
        f"Gerando dica visual para a palavra: '{palavra}' (tipo: {tipo})")

    palavra = palavra.lower().strip()

    # Dicionário de emojis para algumas palavras comuns
    emojis = {
        "casa": "🏠", "cão": "🐕", "gato": "🐱", "cachorro": "🐕", "sol": "☀️", "lua": "🌙",
        "estrela": "⭐", "flor": "🌸", "árvore": "🌳", "peixe": "🐟", "coração": "❤️",
        "água": "💧", "fogo": "🔥", "livro": "📚", "música": "🎵", "carro": "🚗",
        "avião": "✈️", "barco": "🚢", "bola": "⚽", "pão": "🍞", "fruta": "🍎",
        "banana": "🍌", "maçã": "🍎", "laranja": "🍊", "uva": "🍇", "morango": "🍓",
        "leite": "🥛", "café": "☕", "pizza": "🍕", "bolo": "🎂", "doce": "🍬",
        "pássaro": "🐦", "borboleta": "🦋", "cobra": "🐍", "sapo": "🐸", "leão": "🦁",
        "dinheiro": "💰", "telefone": "📱", "computador": "💻", "carta": "✉️", "presente": "🎁",
        "bebê": "👶", "menino": "👦", "menina": "👧", "homem": "👨", "mulher": "👩",
        "mão": "👋", "olho": "👁️", "nariz": "👃", "boca": "👄", "orelha": "👂"
    }

    # Selecionar com base no tipo
    if tipo == "emoji":
        # Retornar emoji se disponível, ou um genérico
        return {"palavra": palavra, "dica_visual": emojis.get(palavra, "📝"), "tipo": "emoji"}

    elif tipo == "url":
        # Em uma implementação real, isso poderia usar uma API de imagens
        # Aqui estamos apenas simulando com um placeholder
        return {
            "palavra": palavra,
            "dica_visual": f"https://via.placeholder.com/200x200?text={palavra}",
            "tipo": "url"
        }

    else:  # descricao (padrão)
        # Gerar uma descrição simples para uma imagem
        descricao = f"Uma imagem clara de '{palavra}'"

        # Adicionar detalhes com base em categorias comuns
        for tema, palavras in WORD_THEMES.items():
            if palavra in palavras:
                if tema == "animais":
                    descricao = f"Uma imagem de um {palavra} em seu habitat natural"
                elif tema == "alimentos":
                    descricao = f"Uma imagem apetitosa de {palavra} fresco"
                elif tema == "escola":
                    descricao = f"Uma imagem clara de {palavra} usado em ambiente escolar"
                elif tema == "casa":
                    descricao = f"Uma imagem de {palavra} em um ambiente doméstico"
                elif tema == "corpo":
                    descricao = f"Uma ilustração clara mostrando {palavra} humano"
                break

        return {"palavra": palavra, "dica_visual": descricao, "tipo": "descricao"}


@tool_registry.register(
    name="gerar_frase_com_palavra",
    description="Gera uma frase simples contendo a palavra especificada",
    required_params=["palavra"],
    optional_params={"dificuldade": "médio"}
)
def gerar_frase_com_palavra(palavra, dificuldade="médio"):
    """
    Gera uma frase simples contendo a palavra especificada.

    Args:
        palavra: A palavra a ser incluída na frase
        dificuldade: Nível de dificuldade da frase ("iniciante", "médio", "avançado")

    Returns:
        Uma frase contendo a palavra
    """
    logger.info(
        f"Gerando frase com a palavra: '{palavra}' (dificuldade: {dificuldade})")

    palavra = palavra.lower().strip()

    # Frases básicas pré-definidas para diferentes níveis de dificuldade
    frases_iniciante = [
        f"Eu vejo um(a) {palavra}.",
        f"O(A) {palavra} é bonito(a).",
        f"Esse(a) é meu(minha) {palavra}.",
        f"Eu gosto de {palavra}.",
        f"Onde está o(a) {palavra}?",
        f"Este(a) {palavra} é meu(minha).",
        f"O(A) {palavra} é grande."
    ]

    frases_medio = [
        f"Ontem eu comprei um(a) {palavra} novo(a).",
        f"Minha mãe gosta muito de {palavra}.",
        f"Na escola tem um(a) {palavra} colorido(a).",
        f"O(A) {palavra} está na minha casa.",
        f"Você já viu este(a) {palavra} antes?",
        f"Eu quero brincar com o(a) {palavra}.",
        f"Nós vimos um(a) {palavra} no parque."
    ]

    frases_avancado = [
        f"Quando fui ao shopping, encontrei um(a) {palavra} incrível que estava em promoção.",
        f"O(A) professor(a) explicou sobre o(a) {palavra} durante a aula de ciências.",
        f"Durante as férias, minha família e eu descobrimos um(a) {palavra} interessante.",
        f"Você sabia que o(a) {palavra} pode ser utilizado(a) de diferentes maneiras?",
        f"Antigamente, o(a) {palavra} era considerado(a) muito importante pelas pessoas.",
        f"Depois de muito tempo procurando, finalmente encontrei o(a) {palavra} perfeito(a).",
        f"Na próxima semana, irei apresentar um trabalho sobre {palavra} para toda a turma."
    ]

    # Selecionar frase com base na dificuldade
    if dificuldade == "iniciante":
        frase = random.choice(frases_iniciante)
    elif dificuldade == "avançado":
        frase = random.choice(frases_avancado)
    else:  # médio (padrão)
        frase = random.choice(frases_medio)

    return {
        "palavra": palavra,
        "frase": frase,
        "dificuldade": dificuldade
    }


@tool_registry.register(
    name="analisar_desempenho_usuario",
    description="Analisa o desempenho do usuário em exercícios de fala",
    required_params=["historico_exercicios"],
    optional_params={"periodo": "ultimo_mes"}
)
def analisar_desempenho_usuario(historico_exercicios: List[Dict[str, Any]], periodo: str = "ultimo_mes") -> Dict[str, Any]:
    """
    Analisa o desempenho do usuário em exercícios de fala para identificar padrões e áreas de melhoria.

    Args:
        historico_exercicios: Lista de exercícios realizados com resultados
        periodo: Período de análise ("ultimo_mes", "ultima_semana", "todos")

    Returns:
        Análise detalhada do desempenho com métricas e recomendações
    """
    logger.info(f"Analisando desempenho do usuário para período: {periodo}")

    analise = {
        "metricas": {
            "total_exercicios": 0,
            "taxa_acerto": 0.0,
            "sons_problematicos": {},
            "padrao_progresso": "estavel"
        },
        "areas_melhoria": [],
        "pontos_fortes": [],
        "recomendacoes": []
    }

    if not historico_exercicios:
        return analise

    # Análise de métricas básicas
    analise["metricas"]["total_exercicios"] = len(historico_exercicios)

    # Análise de sons problemáticos e taxa de acerto
    for exercicio in historico_exercicios:
        som = exercicio.get("som_alvo", "")
        acerto = exercicio.get("acerto", False)

        if som:
            if som not in analise["metricas"]["sons_problematicos"]:
                analise["metricas"]["sons_problematicos"][som] = {
                    "total": 0, "acertos": 0}

            analise["metricas"]["sons_problematicos"][som]["total"] += 1
            if acerto:
                analise["metricas"]["sons_problematicos"][som]["acertos"] += 1

    # Calcular taxa de acerto geral
    total_acertos = sum(
        1 for ex in historico_exercicios if ex.get("acerto", False))
    analise["metricas"]["taxa_acerto"] = (
        total_acertos / len(historico_exercicios)) * 100

    # Identificar sons problemáticos
    for som, stats in analise["metricas"]["sons_problematicos"].items():
        taxa_acerto = (stats["acertos"] / stats["total"]) * 100
        if taxa_acerto < 60:
            analise["areas_melhoria"].append(
                f"Som '{som}' (taxa de acerto: {taxa_acerto:.1f}%)")
        elif taxa_acerto > 80:
            analise["pontos_fortes"].append(
                f"Som '{som}' (taxa de acerto: {taxa_acerto:.1f}%)")

    return analise


@tool_registry.register(
    name="recomendar_estrategia",
    description="Recomenda estratégias personalizadas de terapia",
    required_params=["analise_desempenho"],
    optional_params={"nivel_atual": "médio"}
)
def recomendar_estrategia(analise_desempenho: Dict[str, Any], nivel_atual: str = "médio") -> Dict[str, Any]:
    """
    Recomenda estratégias personalizadas baseadas na análise de desempenho.

    Args:
        analise_desempenho: Resultado da análise de desempenho do usuário
        nivel_atual: Nível atual do usuário

    Returns:
        Estratégias recomendadas e ajustes sugeridos
    """
    logger.info(f"Gerando recomendações para nível: {nivel_atual}")

    recomendacoes = {
        "estrategias_gerais": [],
        "exercicios_recomendados": [],
        "ajustes_dificuldade": {},
        "foco_proximo_nivel": []
    }

    # Análise de áreas de melhoria
    if analise_desempenho["areas_melhoria"]:
        for area in analise_desempenho["areas_melhoria"]:
            som = area.split("'")[1] if "'" in area else ""
            if som:
                # Buscar exercícios específicos para o som
                exercicios = buscar_palavras_com_som(
                    som, dificuldade=nivel_atual, quantidade=3)
                recomendacoes["exercicios_recomendados"].extend(
                    exercicios.get("palavras", []))

    # Definir estratégias gerais baseadas no desempenho
    taxa_acerto = analise_desempenho["metricas"]["taxa_acerto"]
    if taxa_acerto < 50:
        recomendacoes["estrategias_gerais"].append(
            "Focar em exercícios mais básicos")
        recomendacoes["ajustes_dificuldade"] = {
            "sugestao": "reduzir", "motivo": "taxa de acerto baixa"}
    elif taxa_acerto > 80:
        recomendacoes["estrategias_gerais"].append(
            "Aumentar gradualmente a dificuldade")
        recomendacoes["ajustes_dificuldade"] = {
            "sugestao": "aumentar", "motivo": "alto desempenho"}

    return recomendacoes


@tool_registry.register(
    name="adaptar_dificuldade",
    description="Adapta dinamicamente a dificuldade dos exercícios",
    required_params=["desempenho_atual", "parametros_exercicio"],
    optional_params={"historico_adaptacoes": None}
)
def adaptar_dificuldade(desempenho_atual: Dict[str, Any], parametros_exercicio: Dict[str, Any],
                        historico_adaptacoes: Optional[List] = None) -> Dict[str, Any]:
    """
    Adapta dinamicamente a dificuldade dos exercícios com base no desempenho.

    Args:
        desempenho_atual: Métricas de desempenho atual
        parametros_exercicio: Parâmetros atuais do exercício
        historico_adaptacoes: Histórico de adaptações anteriores

    Returns:
        Novos parâmetros adaptados para o exercício
    """
    logger.info("Adaptando dificuldade do exercício")

    adaptacao = {
        "parametros_anteriores": parametros_exercicio.copy(),
        "parametros_novos": parametros_exercicio.copy(),
        "motivo_adaptacao": "",
        "nivel_adaptacao": "leve"
    }

    taxa_acerto = desempenho_atual.get("taxa_acerto", 0)

    # Regras de adaptação
    if taxa_acerto > 85:
        adaptacao["nivel_adaptacao"] = "aumentar"
        adaptacao["motivo_adaptacao"] = "alto desempenho consistente"

        # Aumentar complexidade
        if "quantidade" in adaptacao["parametros_novos"]:
            adaptacao["parametros_novos"]["quantidade"] += 1

        if "dificuldade" in adaptacao["parametros_novos"]:
            nivel_atual = adaptacao["parametros_novos"]["dificuldade"]
            if nivel_atual == "iniciante":
                adaptacao["parametros_novos"]["dificuldade"] = "médio"
            elif nivel_atual == "médio":
                adaptacao["parametros_novos"]["dificuldade"] = "avançado"

    elif taxa_acerto < 40:
        adaptacao["nivel_adaptacao"] = "reduzir"
        adaptacao["motivo_adaptacao"] = "dificuldade elevada para o nível atual"

        # Reduzir complexidade
        if "quantidade" in adaptacao["parametros_novos"]:
            adaptacao["parametros_novos"]["quantidade"] = max(
                3, adaptacao["parametros_novos"]["quantidade"] - 1)

        if "dificuldade" in adaptacao["parametros_novos"]:
            nivel_atual = adaptacao["parametros_novos"]["dificuldade"]
            if nivel_atual == "avançado":
                adaptacao["parametros_novos"]["dificuldade"] = "médio"
            elif nivel_atual == "médio":
                adaptacao["parametros_novos"]["dificuldade"] = "iniciante"

    return adaptacao


# Exportar todas as funções disponíveis
__all__ = [
    "buscar_palavras_com_som",
    "buscar_palavras_por_tema",
    "avaliar_dificuldade_palavra",
    "gerar_dica_visual",
    "gerar_frase_com_palavra",
    "analisar_desempenho_usuario",
    "recomendar_estrategia",
    "adaptar_dificuldade"
]
