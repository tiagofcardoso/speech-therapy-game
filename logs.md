# Speech Therapy Game System Logs

This document contains formatted logs from the speech therapy game system, showing agent interactions and system processes.

## Table of Contents
- [System Initialization](#system-initialization)
- [Game Generation](#game-generation)
- [Game Session](#game-session)
- [Speech Evaluation](#speech-evaluation)

## System Initialization

Server startup and initialization of key components:

```bash
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
```

## Agent Initialization

Agent startup and configuration:

```plaintext
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
```

## Game Generation

Game generation process by the Game Designer agent:

```plaintext
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
```

### Progression Manager Determines Difficulty

```plaintext
2025-04-24 11:33:03,988 - ai.server.mcp_coordinator - INFO - Handling message for game_designer: create_game
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] Determining difficulty for user profile
2025-04-24 11:33:04,002 - agent.progression - INFO - Determining difficulty for user profile
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] Analyzing 163 completed sessions
2025-04-24 11:33:04,002 - agent.progression - INFO - Analyzing 163 completed sessions
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] User unknown average score: 61.333333333333336 from 3 recent sessions
2025-04-24 11:33:04,002 - agent.progression - INFO - User unknown average score: 61.333333333333336 from 3 recent sessions
2025-04-24 11:33:04 - agent.progression - INFO - [AGENT:PROGRESSION] Difficulty determination complete: médio
2025-04-24 11:33:04,002 - agent.progression - INFO - Difficulty determination complete: médio
```

### Game Creation by Game Designer

```plaintext
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
```

## Game Session

Game session initialization and loading:

```plaintext
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
```

## Speech Synthesis

Text-to-speech generation for game words:

```plaintext
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
```

## Speech Evaluation

The speech recognition and evaluation process:

```plaintext
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
```

### Agent Interaction During Evaluation

```plaintext
2025-04-24 11:33:28,244 - ai.server.mcp_coordinator - INFO - Avaliando pronúncia: palavra='Elefante', user_id=67fac68b22daf9e00d6b967e, session_id=55347b1c-36b8-4e23-add0-2bc2259d6f12
2025-04-24 11:33:28,244 - utils.agent_diagnostics - INFO - === AGENT INTERACTION SESSION STARTED: 55347b1c-36b8-4e23-add0-2bc2259d6f12 ===
2025-04-24 11:33:28,244 - utils.agent_diagnostics - INFO - [AGENT:MCP_COORDINATOR] → [AGENT:SPEECH_EVALUATOR] evaluate_pronunciation_request
2025-04-24 11:33:28,244 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Sending evaluation request to speech_evaluator agent
2025-04-24 11:33:28,244 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Processing message via speech_evaluator agent
2025-04-24 11:33:28,244 - ai.server.mcp_coordinator - INFO - Handling message for speech_evaluator: evaluate_pronunciation
2025-04-24 11:33:28 - agent.speech_evaluator - INFO - [AGENT:SPEECH_EVALUATOR] Agent initialized
```

### Speech Recognition Process

```plaintext
2025-04-24 11:33:28,251 - ai.server.mcp_coordinator - INFO - Áudio salvo temporariamente em: /tmp/tmpcrrt82ss.webm
2025-04-24 11:33:28,251 - ai.server.mcp_coordinator - INFO - Convertendo áudio: ffmpeg -i /tmp/tmpcrrt82ss.webm -y /tmp/tmpcrrt82ss.wav
2025-04-24 11:33:28,369 - ai.server.mcp_coordinator - INFO - Áudio convertido para WAV: /tmp/tmpcrrt82ss.wav
2025-04-24 11:33:28,370 - ai.server.mcp_coordinator - INFO - Duração do áudio: 2.4 segundos
2025-04-24 11:33:28,370 - ai.server.mcp_coordinator - INFO - Tipo da função recognize_speech: <class 'function'>
2025-04-24 11:33:28,370 - ai.server.mcp_coordinator - INFO - Tentando reconhecer áudio do arquivo: /tmp/tmpcrrt82ss.wav
2025-04-24 11:33:28,370 - ai.server.mcp_coordinator - INFO - Com idioma: pt-PT
2025-04-24 11:33:28,840 - ai.server.mcp_coordinator - INFO - Google Speech Recognition: 'elefante'
2025-04-24 11:33:28,840 - ai.server.mcp_coordinator - INFO - Texto reconhecido final: 'elefante'
```

### File Cleanup and Feedback Generation

```plaintext
2025-04-24 11:33:28,840 - ai.server.mcp_coordinator - INFO - Arquivo temporário removido: /tmp/tmpcrrt82ss.webm
2025-04-24 11:33:28,840 - ai.server.mcp_coordinator - INFO - Arquivo temporário WAV removido: /tmp/tmpcrrt82ss.wav
🔊 Configurações de voz: {'language_code': 'pt-PT'}
✅ Áudio sintetizado com gTTS. Tamanho: 32064 bytes
2025-04-24 11:33:29,140 - ai.server.mcp_coordinator - INFO - Áudio de feedback gerado com sucesso (42752 caracteres)
```

### Evaluation Result and Session Completion

```plaintext
2025-04-24 11:33:29,140 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Received response from speech_evaluator agent
2025-04-24 11:33:29,140 - utils.agent_diagnostics - INFO - [AGENT:SPEECH_EVALUATOR] → [AGENT:MCP_COORDINATOR] evaluate_pronunciation_response
2025-04-24 11:33:29,140 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Saving evaluation to database for session 55347b1c-36b8-4e23-add0-2bc2259d6f12
2025-04-24 11:33:29,141 - ai.server.mcp_coordinator - INFO - [COORDINATOR] Avaliação salva no banco de dados para sessão 55347b1c-36b8-4e23-add0-2bc2259d6f12
2025-04-24 11:33:29,141 - utils.agent_diagnostics - INFO - === AGENT INTERACTION SESSION ENDED: 55347b1c-36b8-4e23-add0-2bc2259d6f12 (2 interactions) ===
```

## Final Evaluation Result

The final evaluation result showing a successful pronunciation:

```json
✅ Resultado da avaliação: {
  "success": true,
  "isCorrect": true,
  "score": 10,
  "recognized_text": "elefante",
  "feedback": "Excelente pronúncia de 'Elefante'! Perfeito!",
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
```