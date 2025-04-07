import openai
from ai.openai_client import create_openai_client  # Nova importação
import os
import random
import json
from typing import Optional, Dict, List, Any
import datetime

class GameGenerator:
    def __init__(self):
        """Initialize game generator"""
        # Substitua a inicialização direta pelo novo método
        self.client = create_openai_client()
        
        self.difficulty_levels = ["beginner", "intermediate", "advanced"]
        self.game_types = ["articulation", "vocabulary", "fluency", "pragmatic"]
        self.current_games = {}
    
    def create_game(self, user_id: str, difficulty: Optional[str] = None, game_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new speech therapy game
        
        Parameters:
        user_id (str): User identifier
        difficulty (str, optional): Game difficulty level
        game_type (str, optional): Type of speech therapy game
        
        Returns:
        Dict: Game data
        """
        # If no difficulty specified, determine based on user history
        if not difficulty:
            difficulty = self._get_user_difficulty(user_id)
            
        # If no game type specified, determine based on user needs
        if not game_type:
            game_type = self._get_appropriate_game_type(user_id)
        
        # Generate game content based on difficulty and type
        game_content = self._generate_content(difficulty, game_type)
        
        # Generate unique game ID
        game_id = f"{random.randint(1000, 9999)}"
        
        # Store game state
        self.current_games[user_id] = {
            "game_id": game_id,
            "difficulty": difficulty,
            "game_type": game_type,
            "content": game_content,
            "current_index": 0,
            "score": 0,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # Return game data
        return {
            "game_id": game_id,
            "difficulty": difficulty,
            "game_type": game_type,
            "title": game_content.get("title", f"Jogo de {game_type.capitalize()}"),
            "description": game_content.get("description", "Exercício de terapia da fala"),
            "instructions": game_content.get("instructions", "Siga as instruções do jogo"),
            "content": game_content.get("exercises", []),
            "metadata": {
                "target_skills": game_content.get("target_skills", []),
                "estimated_duration": game_content.get("estimated_duration", "5-10 minutos")
            }
        }
    
    def _get_user_difficulty(self, user_id: str) -> str:
        """Determine appropriate difficulty level based on user history"""
        # TODO: Query the database for user history and progress
        # For now, default to beginner
        return "beginner"
    
    def _get_appropriate_game_type(self, user_id: str) -> str:
        """Determine the most appropriate game type based on user needs"""
        # TODO: Analyze user performance data to determine focus areas
        # For now, return a random game type
        return random.choice(self.game_types)
    
    def _generate_content(self, difficulty: str, game_type: str) -> Dict[str, Any]:
        """Generate game content using OpenAI"""
        try:
            # Verificar se o cliente OpenAI está disponível
            if self.client is None:
                print("Cliente OpenAI não disponível. Usando conteúdo de fallback.")
                return self._get_fallback_content(game_type, difficulty)
            
            # Create system prompt based on game type
            system_prompt = self._create_system_prompt(game_type, difficulty)
            
            user_prompt = f"""
            Crie um jogo de terapia da fala do tipo '{game_type}' com nível de dificuldade '{difficulty}'.
            O jogo deve ser adequado para crianças falantes de português.
            Inclua um título criativo, descrição, instruções claras e 5 exercícios.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            try:
                content_str = response.choices[0].message.content
                content_json = json.loads(content_str)
                return content_json
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from OpenAI response: {e}")
                return self._get_fallback_content(game_type, difficulty)
                
        except Exception as e:
            print(f"Error generating content: {str(e)}")
            return self._get_fallback_content(game_type, difficulty)
    
    def _create_system_prompt(self, game_type: str, difficulty: str) -> str:
        """Create appropriate system prompt based on game type"""
        base_prompt = """Você é um especialista em terapia da fala para crianças falantes de português.
        
# CONTEXTO
Você está criando jogos para uma aplicação de terapia da fala que ajuda crianças a melhorar suas habilidades de comunicação.
O jogo deve ser adequado para o nível de dificuldade especificado e se concentrar no tipo de exercício solicitado.

# FORMATO DE SAÍDA
Responda com um objeto JSON contendo:
- "title": título criativo do jogo
- "description": breve descrição do objetivo do jogo
- "instructions": instruções claras para jogar
- "target_skills": array de habilidades específicas que o jogo desenvolve
- "estimated_duration": tempo estimado para completar o jogo
- "exercises": array com 5 exercícios específicos
"""

        if game_type == "articulation":
            return base_prompt + """
# TIPO DE JOGO: ARTICULAÇÃO
Crie jogos focados na pronúncia correta de sons específicos do português.

# EXEMPLOS DE JOGOS DE ARTICULAÇÃO
1. "O que é o que é?": Adivinhas focando em palavras com sons específicos
2. "Jogo da Memória dos Sons": Pares de cartões com imagens de objetos contendo o som-alvo
3. "Twister de Línguas": Trava-línguas para praticar sons específicos
4. "Adivinhe o Som": Identificação de sons específicos
5. "Construindo Palavras": Usar letras para construir palavras com o som-alvo

Cada exercício deve incluir:
- "title": título do exercício
- "target_sound": som-alvo (ex: /r/, /s/, "lh", "nh")
- "description": descrição do exercício
- "words": lista de palavras com o som-alvo
- "activity": instrução específica para a atividade
"""

        elif game_type == "vocabulary":
            return base_prompt + """
# TIPO DE JOGO: VOCABULÁRIO E LINGUAGEM
Crie jogos focados no desenvolvimento do vocabulário e habilidades linguísticas.

# EXEMPLOS DE JOGOS DE VOCABULÁRIO
1. "Jogo das Categorias": Nomear itens dentro de categorias específicas
2. "Contar Histórias": Usar cartões ou indicações para criar histórias
3. "Oposto": Dizer o oposto de uma palavra
4. "Descreva a Imagem": Descrever imagens usando frases completas
5. "Jogo do Sinônimo": Dizer sinônimos para palavras

Cada exercício deve incluir:
- "title": título do exercício
- "category": categoria semântica (ex: animais, alimentos, ações)
- "description": descrição do exercício
- "words_or_prompts": lista de palavras ou indicações para o exercício
- "activity": instrução específica para a atividade
"""

        elif game_type == "fluency":
            return base_prompt + """
# TIPO DE JOGO: FLUÊNCIA
Crie jogos focados no desenvolvimento da fluência verbal.

# EXEMPLOS DE JOGOS DE FLUÊNCIA
1. "Cantar em Coro": Cantar músicas infantis portuguesas
2. "Leitura em Eco": Adulto lê uma frase e criança repete
3. "Respiração e Relaxamento": Exercícios de respiração para promover relaxamento
4. "Leitura Rítmica": Ler um texto seguindo um ritmo
5. "Conversa Telefônica": Simular conversas telefônicas

Cada exercício deve incluir:
- "title": título do exercício
- "technique": técnica de fluência utilizada
- "description": descrição do exercício
- "script_or_text": texto ou roteiro para o exercício
- "activity": instrução específica para a atividade
"""

        else:  # pragmatic
            return base_prompt + """
# TIPO DE JOGO: LINGUAGEM PRAGMÁTICA (HABILIDADES SOCIAIS)
Crie jogos focados no desenvolvimento de habilidades sociais e comunicação pragmática.

# EXEMPLOS DE JOGOS PRAGMÁTICOS
1. "Jogo de Papéis": Simular diferentes situações sociais
2. "Jogo das Emoções": Identificar e discutir diferentes emoções
3. "Completar a História": Adicionar elementos a uma história, focando em interações sociais
4. "Jogo das Perguntas": Praticar perguntas e respostas em contexto social
5. "Jogo da Empatia": Apresentar cenários e discutir sentimentos e reações

Cada exercício deve incluir:
- "title": título do exercício
- "social_context": contexto social do exercício
- "description": descrição do exercício
- "scenario": cenário ou situação para o exercício
- "activity": instrução específica para a atividade
"""

    def _get_fallback_content(self, game_type: str, difficulty: str) -> Dict[str, Any]:
        """Return fallback content if API fails"""
        if game_type == "articulation":
            return {
                "title": "Caça aos Sons",
                "description": "Um jogo para praticar sons específicos do português",
                "instructions": "Pronuncie cada palavra com atenção ao som destacado",
                "target_skills": ["articulação", "consciência fonológica"],
                "estimated_duration": "5-10 minutos",
                "exercises": [
                    {
                        "title": "O Som do R",
                        "target_sound": "/r/",
                        "description": "Pratique o som do R",
                        "words": ["rato", "roda", "rua", "carro", "borracha"],
                        "activity": "Repita cada palavra e tente identificar onde o som do R aparece"
                    }
                ]
            }
        elif game_type == "vocabulary":
            return {
                "title": "Mundo dos Animais",
                "description": "Explore o vocabulário relacionado aos animais",
                "instructions": "Responda às perguntas sobre os animais utilizando frases completas",
                "target_skills": ["vocabulário", "formação de frases"],
                "estimated_duration": "5-10 minutos",
                "exercises": [
                    {
                        "title": "Animais da Fazenda",
                        "category": "animais",
                        "description": "Nomeie animais que vivem na fazenda",
                        "words_or_prompts": ["vaca", "cavalo", "galinha", "porco", "ovelha"],
                        "activity": "Diga o nome de cada animal e um som que ele faz"
                    }
                ]
            }
        elif game_type == "fluency":
            return {
                "title": "Ritmo da Fala",
                "description": "Exercícios para melhorar a fluência verbal",
                "instructions": "Siga o ritmo e pratique falar com calma e fluidez",
                "target_skills": ["fluência", "ritmo da fala"],
                "estimated_duration": "5-10 minutos",
                "exercises": [
                    {
                        "title": "Canção do Alfabeto",
                        "technique": "canto rítmico",
                        "description": "Cantar o alfabeto ajuda a manter um ritmo constante na fala",
                        "script_or_text": "A B C D E F G, H I J K L M N O P, Q R S T U V, W X Y Z",
                        "activity": "Cante o alfabeto seguindo um ritmo lento e constante"
                    }
                ]
            }
        else:  # pragmatic
            return {
                "title": "Conversas do Dia a Dia",
                "description": "Pratique habilidades de conversação para situações cotidianas",
                "instructions": "Imagine-se nas situações descritas e pratique as respostas adequadas",
                "target_skills": ["habilidades sociais", "comunicação pragmática"],
                "estimated_duration": "10-15 minutos",
                "exercises": [
                    {
                        "title": "Na Loja",
                        "social_context": "compras",
                        "description": "Aprenda a interagir em uma situação de compra",
                        "scenario": "Você está em uma loja e quer comprar um brinquedo",
                        "activity": "Pratique como pedir ajuda ao vendedor e fazer perguntas sobre o brinquedo"
                    }
                ]
            }