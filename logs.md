(usr) tiagocardoso@Fedora:~/Projects/speech-therapy-game/backend$ python app.py
Carregando variáveis de ambiente de: /home/tiagocardoso/Projects/speech-therapy-game/.env
MongoDB URI (com credenciais escapadas): mongodb://admin:Ti%40go150283@localhost:27017/speech_therapy_db?authSource=admin
Connected to MongoDB successfully
Connected to MongoDB successfully
Connected to MongoDB successfully
which: no rhubarb in (/home/tiagocardoso/.vscode/extensions/ms-python.python-2025.4.0-linux-x64/python_files/deactivate/bash:/usr/bin:/usr/condabin:/usr/local/bin:/usr/local/bin:/home/tiagocardoso/.vscode/extensions/ms-python.python-2025.4.0-linux-x64/python_files/deactivate/bash:/usr/bin:/usr/condabin:/usr/local/bin:/usr/local/bin:/home/tiagocardoso/.cargo/bin:/usr/local/bin:/usr/local/bin:/home/tiagocardoso/.local/bin:/home/tiagocardoso/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/var/lib/snapd/snap/bin:/home/tiagocardoso/.cache/lm-studio/bin:/home/tiagocardoso/Android/flutter/bin:/opt/mssql-tools/bin:/home/tiagocardoso/.cache/lm-studio/bin:/home/tiagocardoso/Android/flutter/bin:/home/tiagocardoso/.cache/lm-studio/bin:/home/tiagocardoso/Android/flutter/bin:/opt/mssql-tools/bin:/home/tiagocardoso/.cache/lm-studio/bin:/home/tiagocardoso/Android/flutter/bin:/home/tiagocardoso/.cache/lm-studio/bin:/home/tiagocardoso/Android/flutter/bin:/opt/mssql-tools/bin)
2025-04-24 11:32:48,015 - speech.lipsync - WARNING - Rhubarb Lip Sync not found. Lipsync generation will use fallback method.
Sentry monitoring disabled (no SENTRY_DSN provided)
Starting server with Uvicorn (via app.py) on port 5001...
INFO:     Started server process [67625]
INFO:     Waiting for application startup.
INFO:     ASGI 'lifespan' protocol appears unsupported.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5001 (Press CTRL+C to quit)
2025-04-24 11:32:55 - agent.game_designer - INFO - [AGENT:GAME_DESIGNER] Agent initialized
2025-04-24 11:32:55,201 - agent.game_designer - INFO - Agent initialized
2025-04-24 11:32:55,219 - ai.server.openai_client - INFO - Async OpenAI client initialized successfully
2025-04-24 11:32:55,219 - utils.language_utils - INFO - Loaded Portuguese word dictionary with 44 entries
2025-04-24 11:32:55,220 - ai.agents.game_designer_agent - INFO - Loaded PT-PT/PT-BR language examples for improved prompting
2025-04-24 11:32:55,228 - ai.server.openai_client - INFO - Async OpenAI client initialized successfully
2025-04-24 11:32:55,229 - ai.server.mcp_coordinator - INFO - OpenAI client initialized successfully.
2025-04-24 11:32:55,229 - ai.server.mcp_coordinator - INFO - Defining tools...
2025-04-24 11:32:55,229 - ai.server.mcp_coordinator - INFO - Defining tools...
2025-04-24 11:32:55,229 - ai.server.mcp_coordinator - INFO - Tools defined.
2025-04-24 11:32:55,229 - ai.server.mcp_coordinator - INFO - Tools defined.
2025-04-24 11:32:55,229 - ai.server.mcp_coordinator - INFO - Registering agents...
2025-04-24 11:32:55,229 - ai.server.mcp_server - INFO - Registered handler for agent: game_designer
2025-04-24 11:32:55,229 - ai.server.mcp_server - INFO - Registered handler for agent: tutor
2025-04-24 11:32:55,229 - ai.server.mcp_server - INFO - Registered handler for agent: speech_evaluator
2025-04-24 11:32:55,229 - ai.server.mcp_coordinator - INFO - Agents registered.
2025-04-24 11:32:55,229 - ai.server.mcp_coordinator - INFO - MCPSystem initialized successfully.
MCP System initialized with database connection
INFO:     127.0.0.1:53308 - "OPTIONS /api/health?_t=1745490775189 HTTP/1.1" 200 OK
INFO:     127.0.0.1:53308 - "GET /api/health?_t=1745490775189 HTTP/1.1" 200 OK
INFO:     127.0.0.1:48946 - "OPTIONS /api/gigi/generate-game?_t=1745490783981 HTTP/1.1" 200 OK
Token recebido: eyJhbGciOiJIUzI...
Decodificando token com chave: 9f42e347d8...
Token decodificado: {'user_id': '67fac68b22daf9e00d6b967e', 'exp': 1745569036, 'iat': 1745482636}
User ID extraído do token: 67fac68b22daf9e00d6b967e
✅ Usuário encontrado: Tiago
✅ Iniciando geração de jogo via Gigi para usuário: 67fac68b22daf9e00d6b967e
📝 Dados da requisição: {'difficulty': '', 'game_type': 'exercícios de pronúncia'}
🔄 Preparando solicitação de jogo: dificuldade=auto (auto=usar progressão do usuário), tipo=exercícios de pronúncia
⏱️ Configurando timeout para criação de jogo: 40 segundos
🔄 Processando mensagem: create_game
2025-04-24 11:33:03,988 - ai.server.mcp_coordinator - INFO - Handling message for game_designer: create_game
2025-04-24 11:33:03 - agent.game_designer - INFO - [AGENT:GAME_DESIGNER] Agent initialized
2025-04-24 11:33:03,988 - agent.game_designer - INFO - Agent initialized
2025-04-24 11:33:03,994 - utils.language_utils - INFO - Loaded Portuguese word dictionary with 44 entries
2025-04-24 11:33:03,994 - ai.agents.game_designer_agent - INFO - Loaded PT-PT/PT-BR language examples for improved prompting
2025-04-24 11:33:03 - agent.gamedesigner - INFO - [AGENT:GAMEDESIGNER] Starting initialize()
2025-04-24 11:33:03,994 - agent.gamedesigner - INFO - Starting initialize()
2025-04-24 11:33:03,994 - ai.agents.game_designer_agent - INFO - Initialization complete
2025-04-24 11:33:03 - agent.gamedesigner - INFO - [AGENT:GAMEDESIGNER] Completed initialize → True
2025-04-24 11:33:03,994 - agent.gamedesigner - INFO - Completed initialize → True
2025-04-24 11:33:03 - agent.progression - INFO - [AGENT:PROGRESSION] Agent initialized
2025-04-24 11:33:03,994 - agent.progression - INFO - Agent initialized
2025-04-24 11:33:03 - agent.progression - INFO - [AGENT:PROGRESSION] Progression Manager agent initialized
2025-04-24 11:33:03,999 - agent.progression - INFO - Progression Manager agent initialized
2025-04-24 11:33:04 - agent.progressionmanager - INFO - [AGENT:PROGRESSIONMANAGER] Starting initialize()
2025-04-24 11:33:04,000 - agent.progressionmanager - INFO - Starting initialize()
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] Initialization complete
2025-04-24 11:33:04,000 - agent.progression - INFO - Initialization complete
2025-04-24 11:33:04 - agent.progressionmanager - INFO - [AGENT:PROGRESSIONMANAGER] Completed initialize → True
2025-04-24 11:33:04,000 - agent.progressionmanager - INFO - Completed initialize → True
✅ Usuário encontrado: Tiago
2025-04-24 11:33:04,001 - ai.server.mcp_coordinator - INFO - Retrieved user profile for user: 67fac68b22daf9e00d6b967e
2025-04-24 11:33:04,002 - ai.server.mcp_coordinator - INFO - Using progression manager to determine difficulty for user 67fac68b22daf9e00d6b967e
2025-04-24 11:33:04 - agent.progressionmanager - INFO - [AGENT:PROGRESSIONMANAGER] Starting determine_difficulty (args: 1, kwargs: 0)
2025-04-24 11:33:04,002 - agent.progressionmanager - INFO - Starting determine_difficulty (args: 1, kwargs: 0)
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] Determining difficulty for user profile
2025-04-24 11:33:04,002 - agent.progression - INFO - Determining difficulty for user profile
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] Analyzing 163 completed sessions
2025-04-24 11:33:04,002 - agent.progression - INFO - Analyzing 163 completed sessions
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] ProgressionManagerAgent.determine_difficulty called by MCP coordinator for user unknown
2025-04-24 11:33:04,002 - agent.progression - INFO - ProgressionManagerAgent.determine_difficulty called by MCP coordinator for user unknown
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] User unknown average score: 61.333333333333336 from 3 recent sessions
2025-04-24 11:33:04,002 - agent.progression - INFO - User unknown average score: 61.333333333333336 from 3 recent sessions
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] Difficulty determination complete: médio
2025-04-24 11:33:04,002 - agent.progression - INFO - Difficulty determination complete: médio
2025-04-24 11:33:04 - agent.progressionmanager - INFO - [AGENT:PROGRESSIONMANAGER] Completed determine_difficulty
2025-04-24 11:33:04,002 - agent.progressionmanager - INFO - Completed determine_difficulty
2025-04-24 11:33:04,002 - ai.server.mcp_coordinator - INFO - Difficulty determined by progression manager: médio
2025-04-24 11:33:04,002 - ai.server.mcp_coordinator - INFO - Difficulty determined by progression manager: médio
2025-04-24 11:33:04,002 - ai.server.mcp_coordinator - INFO - Varied game type based on difficulty: jogos de sequência de palavras
2025-04-24 11:33:04 - agent.gamedesigner - INFO - [AGENT:GAMEDESIGNER] Starting create_game(user_id=67fac68b22daf9e00d6b967e, difficulty=médio, game_type=jogos de sequência de palavras)
2025-04-24 11:33:04,002 - agent.gamedesigner - INFO - Starting create_game(user_id=67fac68b22daf9e00d6b967e, difficulty=médio, game_type=jogos de sequência de palavras)
2025-04-24 11:33:04,002 - ai.agents.game_designer_agent - INFO - Creating game for user 67fac68b22daf9e00d6b967e with difficulty: médio, type: jogos de sequência de palavras
2025-04-24 11:33:04,002 - ai.agents.game_designer_agent - INFO - Creating prompt for game type: jogos de sequência de palavras, difficulty: médio
2025-04-24 11:33:04,002 - ai.agents.game_designer_agent - INFO - Creating game for user 67fac68b22daf9e00d6b967e with difficulty: médio, type: jogos de sequência de palavras
2025-04-24 11:33:04,002 - ai.agents.game_designer_agent - INFO - Sending request to language model for game creation
2025-04-24 11:33:17,542 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-04-24 11:33:17,548 - ai.agents.game_designer_agent - INFO - Game created successfully with 5 exercises
2025-04-24 11:33:17 - agent.gamedesigner - INFO - [AGENT:GAMEDESIGNER] Completed create_game → {'title': 'Aventura de Palavras', 'game_type': 'jogos de sequência de palavras', 'difficulty': 'médi...
2025-04-24 11:33:17,549 - agent.gamedesigner - INFO - Completed create_game → {'title': 'Aventura de Palavras', 'game_type': 'jogos de sequência de palavras', 'difficulty': 'médi...
💾 Salvando jogo gerado no banco de dados
INFO:     127.0.0.1:48946 - "POST /api/gigi/generate-game?_t=1745490783981 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59500 - "OPTIONS /api/games/680a136d861c338dbfbe78a5?_t=1745490802589 HTTP/1.1" 200 OK
Token recebido: eyJhbGciOiJIUzI...
Token decodificado: {'user_id': '67fac68b22daf9e00d6b967e', 'exp': 1745569036, 'iat': 1745482636}
User ID extraído do token: 67fac68b22daf9e00d6b967e
✅ Usuário encontrado: Tiago
✅ Usuário encontrado: Tiago
Buscando jogo com ID: 680a136d861c338dbfbe78a5 para usuário: 67fac68b22daf9e00d6b967e
🔍 Buscando jogo no banco de dados com ID: 680a136d861c338dbfbe78a5
Found game: Aventura de Palavras
✅ Jogo encontrado: Aventura de Palavras
🔍 Estrutura do jogo: <class 'dict'>
Erro ao fazer dump do jogo: Object of type datetime is not JSON serializable
🔍 Encontrados 5 exercícios
Primeiro exercício: {'word': 'Elefante', 'prompt': "Repete a palavra e continua com uma palavra que comece com a última sílaba: 'te'.", 'hint': 'Pensa num animal grande que vive na savana.', 'type': 'Sequência de palavras', 'feedback': {'correct': 'Excelente! A palavra está correta.', 'incorrect': "Quase lá! Tenta novamente e pensa numa palavra que comece com 'te'."}}
✅ Retornando jogo transformado com 5 exercícios
INFO:     127.0.0.1:59500 - "GET /api/games/680a136d861c338dbfbe78a5?_t=1745490802589 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59500 - "OPTIONS /api/start_game?_t=1745490802607 HTTP/1.1" 200 OK
Token recebido: eyJhbGciOiJIUzI...
Decodificando token com chave: 9f42e347d8...
Token decodificado: {'user_id': '67fac68b22daf9e00d6b967e', 'exp': 1745569036, 'iat': 1745482636}
User ID extraído do token: 67fac68b22daf9e00d6b967e
✅ Usuário encontrado: Tiago
========== INICIANDO SESSÃO DE JOGO (Rota -> Coordenador) ==========
User ID: 67fac68b22daf9e00d6b967e
Dados recebidos: game_id=680a136d861c338dbfbe78a5, título=Aventura de Palavras, dificuldade=médio
2025-04-24 11:33:22,617 - ai.server.mcp_coordinator - INFO - Loading existing game session for user 67fac68b22daf9e00d6b967e, game 680a136d861c338dbfbe78a5
Found game: Aventura de Palavras
2025-04-24 11:33:22,618 - ai.server.mcp_coordinator - INFO - Found game: Aventura de Palavras
✅ Usuário encontrado: Tiago
2025-04-24 11:33:22,619 - ai.server.mcp_coordinator - INFO - Found 5 exercises
2025-04-24 11:33:22,619 - ai.server.mcp_coordinator - INFO - Handling message for tutor: create_instructions
2025-04-24 11:33:22 - agent.tutor - INFO - [AGENT:TUTOR] Agent initialized
2025-04-24 11:33:22,619 - agent.tutor - INFO - Agent initialized
2025-04-24 11:33:22,625 - TutorAgent - INFO - TutorAgent inicializado com voz ativada
2025-04-24 11:33:22,625 - TutorAgent - INFO - Tutor agent initialized with game designer reference
2025-04-24 11:33:22 - agent.tutor - INFO - [AGENT:TUTOR] Starting initialize()
2025-04-24 11:33:22,625 - agent.tutor - INFO - Starting initialize()
2025-04-24 11:33:22,625 - TutorAgent - INFO - Initialization complete
2025-04-24 11:33:22 - agent.tutor - INFO - [AGENT:TUTOR] Completed initialize → True
2025-04-24 11:33:22,625 - agent.tutor - INFO - Completed initialize → True
2025-04-24 11:33:22,626 - ai.server.mcp_coordinator - INFO - Returning game with 5 exercises
Response structure: {
  "game": {
    "description": "",
    "difficulty": "m\u00e9dio",
    "exercises": [
      {
        "word": "Elefante",
        "prompt": "Repete a palavra e continua com uma palavra que comece com a \u00faltima s\u00edlaba: 'te'.",
        "hint": "Pensa num animal grande que vive na savana.",
        "type": "Sequ\u00eancia de palavras",
        "feedback": {
          "correct": "Excelente! A palavra est\u00e1 correta.",
          "incorrect": "Quase l\u00e1! Tenta novamente e pensa numa palavra que comece com 'te'."
        }
      },
      {
        "word": "M\u00fasica",
        "prompt": "Repete a palavra e une-a com uma palavra que comece com a \u00faltima s\u00edlaba: 'ca'.",
        "hint": "Pensa num tipo de arte que envolve som e melodia.",
        "type": "Sequ\u00eancia de palavras",
        "feedback": {
          "correct": "Muito bem! Fizeste uma boa associa\u00e7\u00e3o.",
          "incorrect": "Boa tentativa! Lembra-te que a pr\u00f3xima palavra deve come\u00e7ar com 'ca'."
        }
      },
      {
        "word": "Estrela",
        "prompt": "Repete a palavra e encontra uma palavra que comece com 'la'.",
        "hint": "\u00c9 algo que brilha no c\u00e9u \u00e0 noite.",
        "type": "Sequ\u00eancia de palavras",
        "feedback": {
          "correct": "Perfeito! Continuas a brilhar como uma estrela.",
          "incorrect": "N\u00e3o desanimes! Pensa em algo que come\u00e7a com 'la'."
        }
      },
      {
        "word": "Computador",
        "prompt": "Repete a palavra e liga-a a uma palavra que comece com 'dor'.",
        "hint": "\u00c9 um aparelho que usamos para trabalhar e jogar.",
        "type": "Sequ\u00eancia de palavras",
        "feedback": {
          "correct": "Est\u00e1 brilhante! A conex\u00e3o entre as palavras est\u00e1 correta.",
          "incorrect": "Quase certo! Lembra-te que a pr\u00f3xima palavra deve come\u00e7ar com 'dor'."
        }
      },
      {
        "word": "Desporto",
        "prompt": "Repete a palavra e segue com uma palavra que inicie com 'to'.",
        "hint": "\u00c9 uma atividade f\u00edsica que pode ser jogada sozinho ou em equipa.",
        "type": "Sequ\u00eancia de palavras",
        "feedback": {
          "correct": "Muito bem! Est\u00e1s a ficar um especialista em sequ\u00eancias.",
          "incorrect": "N\u00e3o te preocupes! Tenta pensar numa palavra que comece com 'to'."
        }
      }
    ],
    "game_id": "680a136d861c338dbfbe78a5",
    "game_type": "jogos de sequ\u00eancia de palavras",
    "instructions": [],
    "metadata": {},
    "title": "Aventura de Palavras"
  },
  "session_id": "55347b1c-36b8-4e23-add0-2bc2259d6f12",
  "success": true,
  "user_info": {
    "name": "Tiago",
    "preferences": {}
  }
}
INFO:     127.0.0.1:59500 - "POST /api/start_game?_t=1745490802607 HTTP/1.1" 200 OK
INFO:     127.0.0.1:59500 - "OPTIONS /api/synthesize?_t=1745490802632 HTTP/1.1" 200 OK
Token recebido: eyJhbGciOiJIUzI...
Decodificando token com chave: 9f42e347d8...
Token decodificado: {'user_id': '67fac68b22daf9e00d6b967e', 'exp': 1745569036, 'iat': 1745482636}
User ID extraído do token: 67fac68b22daf9e00d6b967e
✅ Usuário encontrado: Tiago
📝 Texto para síntese com Polly: 'Elefante'
🔊 Configurações de voz: {'voice_id': 'Ines', 'engine': 'standard', 'language_code': 'pt-PT', 'sample_rate': '22050'}
🔊 Tentando usar Amazon Polly com voz: Ines
2025-04-24 11:33:22,674 - speech.synthesis - INFO - Amazon Polly client initialized
2025-04-24 11:33:22,981 - speech.synthesis - INFO - Successfully synthesized text: 'Elefante...' with Amazon Polly
✅ Áudio sintetizado com Amazon Polly
✅ Áudio Polly gerado: 6332 caracteres
INFO:     127.0.0.1:59500 - "POST /api/synthesize?_t=1745490802632 HTTP/1.1" 200 OK
INFO:     127.0.0.1:52128 - "OPTIONS /api/evaluate-pronunciation?_t=1745490808236 HTTP/1.1" 200 OK
Token recebido: eyJhbGciOiJIUzI...
Decodificando token com chave: 9f42e347d8...
Token decodificado: {'user_id': '67fac68b22daf9e00d6b967e', 'exp': 1745569036, 'iat': 1745482636}
User ID extraído do token: 67fac68b22daf9e00d6b967e
✅ Usuário encontrado: Tiago
📊 Avaliando pronúncia:
- Arquivo de áudio: pronunciation.webm (audio/webm)
- Palavra esperada: 'Elefante'
- ID do usuário: 67fac68b22daf9e00d6b967e
- ID da sessão: 55347b1c-36b8-4e23-add0-2bc2259d6f12
- Tamanho do arquivo: 39123 bytes
2025-04-24 11:33:28,244 - ai.server.mcp_coordinator - INFO - Avaliando pronúncia: palavra='Elefante', user_id=67fac68b22daf9e00d6b967e, session_id=55347b1c-36b8-4e23-add0-2bc2259d6f12
2025-04-24 11:33:28,244 - utils.agent_diagnostics - INFO - === AGENT INTERACTION SESSION STARTED: 55347b1c-36b8-4e23-add0-2bc2259d6f12 ===
2025-04-24 11:33:28,244 - utils.agent_diagnostics - INFO - [AGENT:MCP_COORDINATOR] → [AGENT:SPEECH_EVALUATOR] evaluate_pronunciation_request
2025-04-24 11:33:28,244 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Sending evaluation request to speech_evaluator agent
2025-04-24 11:33:28,244 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Processing message via speech_evaluator agent
2025-04-24 11:33:28,244 - ai.server.mcp_coordinator - INFO - Handling message for speech_evaluator: evaluate_pronunciation
2025-04-24 11:33:28 - agent.speech_evaluator - INFO - [AGENT:SPEECH_EVALUATOR] Agent initialized
2025-04-24 11:33:28,244 - agent.speech_evaluator - INFO - Agent initialized
2025-04-24 11:33:28 - agent.speech_evaluator - INFO - [AGENT:SPEECH_EVALUATOR] SpeechEvaluatorAgent initialized
2025-04-24 11:33:28,250 - agent.speech_evaluator - INFO - SpeechEvaluatorAgent initialized
2025-04-24 11:33:28 - agent.speechevaluator - INFO - [AGENT:SPEECHEVALUATOR] Starting initialize()
2025-04-24 11:33:28,250 - agent.speechevaluator - INFO - Starting initialize()
2025-04-24 11:33:28 - agent.speech_evaluator - INFO - [AGENT:SPEECH_EVALUATOR] Initialization complete
2025-04-24 11:33:28,251 - agent.speech_evaluator - INFO - Initialization complete
2025-04-24 11:33:28 - agent.speechevaluator - INFO - [AGENT:SPEECHEVALUATOR] Completed initialize → True
2025-04-24 11:33:28,251 - agent.speechevaluator - INFO - Completed initialize → True
2025-04-24 11:33:28,251 - ai.server.mcp_coordinator - INFO - Áudio salvo temporariamente em: /tmp/tmpcrrt82ss.webm
2025-04-24 11:33:28,251 - ai.server.mcp_coordinator - INFO - Convertendo áudio: ffmpeg -i /tmp/tmpcrrt82ss.webm -y /tmp/tmpcrrt82ss.wav
2025-04-24 11:33:28,369 - ai.server.mcp_coordinator - INFO - Áudio convertido para WAV: /tmp/tmpcrrt82ss.wav
2025-04-24 11:33:28,370 - ai.server.mcp_coordinator - INFO - Duração do áudio: 2.4 segundos
2025-04-24 11:33:28,370 - ai.server.mcp_coordinator - INFO - Tipo da função recognize_speech: <class 'function'>
2025-04-24 11:33:28,370 - ai.server.mcp_coordinator - INFO - Tentando reconhecer áudio do arquivo: /tmp/tmpcrrt82ss.wav
2025-04-24 11:33:28,370 - ai.server.mcp_coordinator - INFO - Com idioma: pt-PT
2025-04-24 11:33:28,840 - ai.server.mcp_coordinator - INFO - Google Speech Recognition: 'elefante'
2025-04-24 11:33:28,840 - ai.server.mcp_coordinator - INFO - Texto reconhecido final: 'elefante'
2025-04-24 11:33:28,840 - ai.server.mcp_coordinator - INFO - Arquivo temporário removido: /tmp/tmpcrrt82ss.webm
2025-04-24 11:33:28,840 - ai.server.mcp_coordinator - INFO - Arquivo temporário WAV removido: /tmp/tmpcrrt82ss.wav
🔊 Configurações de voz: {'language_code': 'pt-PT'}
✅ Áudio sintetizado com gTTS. Tamanho: 32064 bytes
2025-04-24 11:33:29,140 - ai.server.mcp_coordinator - INFO - Áudio de feedback gerado com sucesso (42752 caracteres)
2025-04-24 11:33:29,140 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Received response from speech_evaluator agent
2025-04-24 11:33:29,140 - utils.agent_diagnostics - INFO - [AGENT:SPEECH_EVALUATOR] → [AGENT:MCP_COORDINATOR] evaluate_pronunciation_response
2025-04-24 11:33:29,140 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Saving evaluation to database for session 55347b1c-36b8-4e23-add0-2bc2259d6f12
2025-04-24 11:33:29,141 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Avaliação salva no banco de dados para sessão 55347b1c-36b8-4e23-add0-2bc2259d6f12
2025-04-24 11:33:29,141 - utils.agent_diagnostics - INFO - === AGENT INTERACTION SESSION ENDED: 55347b1c-36b8-4e23-add0-2bc2259d6f12 (2 interactions) ===
✅ Resultado da avaliação: {
  "success": true,
  "isCorrect": true,
  "score": 10,
  "recognized_text": "elefante",
  "feedback": "Excelente pron\u00fancia de 'Elefante'! Perfeito!",
  "audio_feedback": "<audio_data: 42752 chars>",
  "debug_info": {
    "normalized": {
      "expected": "elefante",
      "recognized": "elefante"
    },
    "no_spaces": {
      "expected": "elefante",
      "recognized": "elefante",
      "match": true
    }
  }
}
INFO:     127.0.0.1:52128 - "POST /api/evaluate-pronunciation?_t=1745490808236 HTTP/1.1" 200 OK