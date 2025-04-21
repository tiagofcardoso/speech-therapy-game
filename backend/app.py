import os
import sys
import json
import datetime
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import logging
import traceback  # Adicionar importação do traceback
import time  # Adicionar importação do time
import uuid
import base64
import tempfile
import subprocess
from ai.agents.speech_evaluator_agent import SpeechEvaluatorAgent
# Import app instance and JWT_SECRET_KEY from config
from config import DEBUG, OPENAI_API_KEY, app, JWT_SECRET_KEY
from bson import ObjectId
from flask.json import JSONEncoder
import jwt
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from speech.recognition import recognize_speech
from speech.synthesis import synthesize_speech, get_example_word_for_phoneme
from speech.lipsync import LipsyncGenerator
from ai.server.mcp_coordinator import MCPCoordinator
from ai.agents.game_designer_agent import GameDesignerAgent as GameGenerator
from auth.auth_service import AuthService
from auth.auth_middleware import token_required
from database.db_connector import DatabaseConnector
from dotenv import load_dotenv
from openai import OpenAI

# Importar o blueprint API
from routes.api import api_bp

from pathlib import Path
# Add project root to Python path
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    # Navigate up to speech-therapy-game
    project_root = current_dir.parent.parent.parent
    sys.path.insert(0, str(project_root))


# Classe para codificar ObjectIds para JSON


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


# Load environment variables
load_dotenv()

# Check for essential configurations
if not OPENAI_API_KEY:
    print("\n⚠️  WARNING: OPENAI_API_KEY not set in environment!")
    print("   The application will fail when calling OpenAI services.")
    print("   Set this in your .env file.\n")

# Initialize Flask app
app = Flask(__name__)

# Registrar o blueprint da API
app.register_blueprint(api_bp, url_prefix='/api')

# Configure CORS globalmente
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

# Configure CORS especificamente para rotas de autenticação
CORS(app,
     resources={r"/api/auth/*": {"origins": "*"}},
     methods=["POST", "OPTIONS"],
     allow_headers=["Content-Type"])

app.static_folder = '../frontend/build'
app.static_url_path = '/'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


# Aplique o encoder personalizado ao Flask app
app.json_encoder = CustomJSONEncoder

# Simple ping endpoint to test the server


@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})

# Root endpoint


@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Speech Therapy Game API", "status": "running"})


@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({"success": True, "message": "Backend API is working!"})


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "message": "API está funcionando corretamente"
    })


# Initialize services
auth_service = AuthService()
db = DatabaseConnector()

# Initialize global instances
game_generator = None
mcp_coordinator = None

# Add this after initializing other services
lipsync_generator = LipsyncGenerator()

# Substitua qualquer inicialização direta do MCPCoordinator


@app.before_request
def initialize_services():
    global game_generator, mcp_coordinator, db

    # Verificar se já estão inicializados
    if game_generator is None or mcp_coordinator is None:
        try:
            # Inicializar serviços
            game_generator = GameGenerator()
            # Passar o db_connector para o MCPCoordinator
            mcp_coordinator = MCPCoordinator(
                api_key=OPENAI_API_KEY, db_connector=db)
            print("MCP Coordinator initialized with database connection")
        except Exception as e:
            print(f"Error initializing services: {str(e)}")


# Configure Sentry
if os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.5,
        environment=os.environ.get('ENVIRONMENT', 'development')
    )
    print("Sentry monitoring initialized")
else:
    print("Sentry monitoring disabled (no SENTRY_DSN provided)")

# Adicione esta função antes das rotas de autenticação


def generate_token(user_id):
    print(f"JWT_SECRET_KEY utilizada: {JWT_SECRET_KEY}")
    """
    Gera um token JWT para o usuário
    
    Args:
        user_id: ID do usuário
        
    Returns:
        str: Token JWT
    """
    try:
        # Defina o payload com user_id e timestamps
        payload = {
            'user_id': str(user_id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow()
        }

        # Use a chave secreta definida em config.py
        token = jwt.encode(
            payload,
            JWT_SECRET_KEY,  # Use a constante do config.py
            algorithm='HS256'
        )

        # Dependendo da versão do PyJWT, pode retornar bytes em vez de string
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
    except Exception as e:
        print(f"Erro ao gerar token: {str(e)}")
        raise

# Authentication routes


@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    # Para depuração
    print("==== Recebida requisição de login ====")
    print(f"Método: {request.method}")

    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.get_json()
        print(f"Dados de login: {data}")

        username = data.get('username')  # Espera username em vez de email
        password = data.get('password')

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username e senha são obrigatórios"
            }), 400

        # Autenticar usuário com username
        user = db.authenticate_user(username, password)

        if not user:
            return jsonify({
                "success": False,
                "message": "Username ou senha inválidos"
            }), 401

        # Gerar token JWT
        token = generate_token(user['_id'])

        return jsonify({
            "success": True,
            "token": token,
            "user_id": str(user['_id']),
            "name": user.get('name', '')
        })
    except Exception as e:
        print(f"Erro de login: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao fazer login: {str(e)}"
        }), 500


@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    # Para depuração
    print("==== Recebida requisição de registro ====")
    print(f"Método: {request.method}")

    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.get_json()
        print(f"Dados de registro: {data}")

        # Validação dos dados
        if not data.get('username') or not data.get('password') or not data.get('name'):
            return jsonify({
                "success": False,
                "message": "Nome, username e senha são obrigatórios"
            }), 400

        # Verificar se username já existe
        if db.user_exists(data.get('username')):
            print(f"Usuário '{data.get('username')}' já existe")
            return jsonify({
                "success": False,
                "message": "Este nome de usuário já está em uso. Por favor, escolha outro."
            }), 409

        # Criar novo usuário
        user_id = db.create_user(data)

        # Gerar token JWT
        token = generate_token(user_id)

        return jsonify({
            "success": True,
            "token": token,
            "user_id": str(user_id),
            "name": data.get('name', '')
        })
    except Exception as e:
        print(f"Erro de registro: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro ao criar conta: {str(e)}"
        }), 500


@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_auth(user_id):
    # If we get here, the token is valid
    return jsonify({"success": True, "valid": True, "user_id": user_id}), 200


@app.route('/api/auth/test-token', methods=['GET'])
def test_token():
    """
    Rota para testar a decodificação de token
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token não encontrado no header'}), 401

    try:
        token = auth_header.split(" ")[1]

        # Imprimir informações para debug
        print(f"Testando token: {token[:10]}...")
        print(f"Chave JWT: {JWT_SECRET_KEY[:5]}...")

        # Tentar decodificar
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])

        return jsonify({
            'success': True,
            'decoded': data,
            'user_id': data.get('user_id')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401

# User profile routes


@app.route('/api/user/profile/<user_id>', methods=['GET'])
@token_required
def get_user_profile(user_id, requesting_user_id):
    try:
        # Adicionar mais logs para depuração
        print(f"Fetching profile for user_id: {user_id}")
        print(f"Requesting user_id: {requesting_user_id}")

        # Verificar se o usuário pode acessar este perfil
        if user_id != requesting_user_id:
            print(
                f"Access denied: {requesting_user_id} trying to access {user_id}")
            return jsonify({"error": "Unauthorized access"}), 403

        # CORREÇÃO: Usar db em vez de db_service
        user = db.get_user_by_id(user_id)

        if not user:
            print(f"User not found: {user_id}")
            return jsonify({"error": "User not found"}), 404

        # Remover senha por segurança
        if "password" in user:
            del user["password"]

        # Dados do perfil a retornar
        user_profile = {
            "name": user.get("name", ""),
            "age": user.get("age", 0),
            "level": user.get("level", "beginner"),
        }

        return jsonify(user_profile), 200
    except Exception as e:
        import traceback
        print(f"Error getting user profile: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/user/profile/<user_id>', methods=['PUT'])
@token_required
def update_user_profile(user_id, requesting_user_id):
    # Check if the requesting user is updating their own profile
    if user_id != requesting_user_id:
        return jsonify({"error": "Unauthorized access to update user profile"}), 403

    data = request.json

    # Define what fields are allowed to be updated
    allowed_fields = ["name", "age"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    success = db.update_user(user_id, update_data)

    if not success:
        return jsonify({"error": "Failed to update user profile"}), 500

    return jsonify({"success": True, "message": "Profile updated successfully"}), 200

# Game routes


@app.route('/api/start_game', methods=['POST'])
@token_required
def start_game(user_id):
    try:
        # Log detalhado para depuração
        print(f"========== INICIANDO SESSÃO DE JOGO ==========")
        print(f"User ID: {user_id}")

        # Obter dados da requisição
        data = request.json
        game_id = data.get('game_id')
        difficulty = data.get('difficulty', 'iniciante')
        title = data.get('title', 'Jogo de Pronúncia')
        game_type = data.get('game_type', 'exercícios de pronúncia')

        print(
            f"Dados recebidos: game_id={game_id}, título={title}, dificuldade={difficulty}")

        # Verificar se o usuário existe - buscar com tratamento de ObjectId
        user = db.get_user_by_id(user_id)

        if not user:
            print(f"⚠️ Usuário não encontrado: {user_id}")
            # Criar um usuário básico para não bloquear o fluxo (apenas em desenvolvimento)
            if app.config.get('DEBUG', False):
                print("Modo DEBUG: Criando usuário temporário para continuar o fluxo")
                temp_user_id = db.save_user({
                    "_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
                    "name": "Usuário Temporário",
                    "username": f"temp_{user_id}",
                    "created_at": datetime.datetime.now(),
                    "history": {}
                })
                user = db.get_user_by_id(temp_user_id)
                print(f"Usuário temporário criado: {temp_user_id}")
            else:
                return jsonify({"error": "Usuário não encontrado"}), 404

        user_profile = {
            "name": user.get('name', 'Amigo'),
            "age": user.get('age', 6),
            "history": user.get('history', {})
        }

        print(f"Perfil do usuário: {user_profile}")

        # Inicializar a sessão
        session_data = {}

        # Se um game_id for fornecido, tentar buscar o jogo na base de dados
        if game_id:
            try:
                game_data = db.get_game(game_id)
                print(
                    f"Jogo encontrado: {game_data.get('title') if game_data else 'Não encontrado'}")

                if game_data:
                    # Usar o jogo existente para criar a sessão em vez de gerar um novo
                    print("Utilizando jogo existente para esta sessão")

                    # Preparar exercícios a partir do conteúdo do jogo
                    exercises = []

                    # Verificar diferentes possíveis localizações para os exercícios
                    content = game_data.get("content", {})
                    if isinstance(content, dict) and "exercises" in content:
                        raw_exercises = content.get("exercises", [])
                    elif isinstance(content, dict) and "content" in content:
                        raw_exercises = content.get("content", [])
                    elif "exercises" in game_data:
                        raw_exercises = game_data.get("exercises", [])
                    elif "content" in game_data and isinstance(game_data.get("content"), list):
                        raw_exercises = game_data.get("content", [])
                    elif isinstance(content, list):
                        raw_exercises = content
                    else:
                        raw_exercises = []

                    # Verificar se temos exercícios válidos
                    if not raw_exercises:
                        print(
                            "⚠️ Nenhum exercício encontrado no jogo. Criando exercícios padrão.")
                        # Criar exercícios padrão com base no título ou tipo de jogo
                        raw_exercises = [
                            {
                                "word": "teste",
                                "prompt": "Pronuncie esta palavra",
                                "hint": "Fale devagar",
                                "visual_cue": "teste"
                            },
                            {
                                "word": "jogo",
                                "prompt": "Diga esta palavra",
                                "hint": "Fale com clareza",
                                "visual_cue": "jogo"
                            }
                        ]

                    # Transformar os exercícios para o formato esperado pela sessão
                    for idx, exercise in enumerate(raw_exercises):
                        if not isinstance(exercise, dict):
                            continue

                        # Obter a palavra do exercício, garantindo que não seja vazia
                        word = exercise.get("word", exercise.get(
                            "text", exercise.get("answer", "")))
                        # Se a palavra for vazia, usar uma palavra padrão com base no índice
                        if not word:
                            word = f"palavra{idx+1}"
                            print(
                                f"⚠️ Palavra vazia detectada no exercício {idx}, usando '{word}' como fallback")

                        transformed_exercise = {
                            "word": word,
                            "prompt": exercise.get("prompt", exercise.get("tip", "Pronuncie esta palavra")),
                            "hint": exercise.get("hint", exercise.get("tip", "Fale devagar")),
                            "visual_cue": exercise.get("visual_cue", word)
                        }
                        exercises.append(transformed_exercise)

                    # Verificar se conseguimos processar ao menos um exercício
                    if not exercises:
                        print(
                            "⚠️ Falha ao processar exercícios. Criando exercício padrão.")
                        exercises = [
                            {
                                "word": "teste",
                                "prompt": "Pronuncie esta palavra",
                                "hint": "Fale devagar",
                                "visual_cue": "teste"
                            }
                        ]

                    # Criar sessão a partir do jogo existente
                    session_data = {
                        "session_id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "game_id": game_id,
                        "game_title": game_data.get("title", title),
                        "difficulty": game_data.get("difficulty", difficulty),
                        "game_type": game_data.get("game_type", game_type),
                        "exercises": exercises,
                        "instructions": game_data.get("instructions", ["Bem-vindo ao jogo de pronúncia!"]),
                        "current_index": 0,
                        "responses": [],
                        "completed": False,
                        "start_time": datetime.datetime.now().isoformat(),
                        "end_time": None
                    }
            except Exception as e:
                print(f"Erro ao buscar jogo {game_id}: {str(e)}")
                traceback.print_exc()
                # Continuar mesmo se o jogo não for encontrado

        # Se a sessão não foi criada a partir de um jogo existente, criar uma nova com o MCP
        if not session_data:
            print("Criando nova sessão de jogo via MCP coordinator")
            session_data = mcp_coordinator.create_game_session(
                user_id, user_profile)

            # Associar a sessão com o jogo que está sendo jogado se um ID foi fornecido
            if game_id:
                session_data["game_id"] = game_id
                session_data["game_title"] = title
                session_data["game_type"] = game_type

        # Adicionar ID de sessão para rastreamento se ainda não existir
        if "session_id" not in session_data:
            session_data["session_id"] = str(uuid.uuid4())

        # Adicionar timestamps
        session_data["created_at"] = datetime.datetime.now().isoformat()
        session_data["user_id"] = user_id

        # Salvar sessão no banco de dados
        session_id = db.save_session(session_data)
        print(f"Sessão criada com ID: {session_id}")

        # Obter primeiro exercício
        if "exercises" in session_data and len(session_data["exercises"]) > 0:
            current_exercise = session_data["exercises"][0]
            # Verificação adicional para garantir que o primeiro exercício tenha uma palavra válida
            if not current_exercise.get("word"):
                current_exercise["word"] = "palavra1"
                print("⚠️ Primeira palavra vazia, substituída por 'palavra1'")
        else:
            print("⚠️ Nenhum exercício encontrado na sessão. Criando exercício padrão.")
            # Criar um exercício padrão se não houver exercícios na sessão
            current_exercise = {
                "word": "teste",
                "prompt": "Pronuncie esta palavra",
                "hint": "Fale devagar",
                "visual_cue": "Uma imagem apareceria aqui"
            }
            session_data["exercises"] = [current_exercise]

        # Criar resposta com instruções de boas-vindas e primeiro exercício
        response = {
            "session_id": session_data["session_id"],
            "instructions": session_data.get("instructions", ["Bem-vindo ao jogo de pronúncia!"]),
            "current_exercise": {
                # Garantir palavra padrão
                "word": current_exercise.get("word", "teste"),
                "prompt": current_exercise.get("prompt", "Pronuncie esta palavra"),
                "hint": current_exercise.get("hint", "Fale devagar"),
                "visual_cue": current_exercise.get("visual_cue", current_exercise.get("word", "teste")),
                "index": 0,
                "total": len(session_data.get("exercises", []))
            }
        }

        print(f"Resposta preparada: {response}")
        print("========== SESSÃO DE JOGO INICIADA COM SUCESSO ==========")

        return jsonify(response), 200
    except Exception as e:
        print(f"❌ Erro ao iniciar jogo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Falha ao iniciar jogo: {str(e)}"}), 500


@app.route('/api/submit_response', methods=['POST'])
@token_required
def submit_response(user_id):
    session_id = request.json.get('session_id')
    recognized_text = request.json.get('recognized_text')

    # Get session from database
    session_data = db.get_session(session_id)
    if not session_data:
        return jsonify({"error": "Session not found"}), 404

    # Verify the session belongs to the authenticated user
    if session_data.get("user_id") != user_id:
        return jsonify({"error": "Unauthorized access to session"}), 403

    # Use MCP to evaluate the response
    evaluation_results = mcp_coordinator.process_response(
        session_data, recognized_text)

    if "session_complete" in evaluation_results and evaluation_results["session_complete"]:
        # Calcular pontuação final
        responses = session_data.get("responses", [])
        total_score = sum(r.get("score", 0) for r in responses)
        exercises_count = len(session_data.get("exercises", []))

        # Evitar divisão por zero
        if exercises_count > 0:
            final_score_percentage = (
                total_score / (exercises_count * 10)) * 100
        else:
            final_score_percentage = 0

        # Verificar se atingiu o mínimo para o nível
        difficulty = session_data.get("difficulty", "iniciante")
        completion_threshold = {
            "iniciante": 80,
            "médio": 90,
            "avançado": 100
        }.get(difficulty, 80)

        # Definir se o jogo foi concluído com base na pontuação mínima
        is_completed = final_score_percentage >= completion_threshold

        # Atualizar no banco de dados
        db.update_session(session_id, {
            "completed": is_completed,
            "final_score": final_score_percentage,
            "completion_status": "completed" if is_completed else "attempted",
            "end_time": datetime.datetime.now().isoformat()
        })

        # Adicionar ao histórico do usuário
        user = db.get_user(user_id)
        if user:
            history = user.get("history", {})
            session_summary = {
                "completed_at": datetime.datetime.now().isoformat(),
                "difficulty": difficulty,
                "exercises_count": exercises_count,
                "score": final_score_percentage,
                "completed": is_completed
            }

            if "completed_sessions" not in history:
                history["completed_sessions"] = []

            history["completed_sessions"].append(session_summary)
            db.update_user(user_id, {"history": history})

        # Retornar resultado com informação sobre conclusão
        return jsonify({
            "session_complete": True,
            "feedback": evaluation_results.get("feedback", {}),
            "final_score": final_score_percentage,
            "passed_threshold": is_completed,
            "completion_status": "completed" if is_completed else "need_improvement",
            "completion_threshold": completion_threshold
        }), 200

    # Resto da função para processar respostas normais...
    # ...


@app.route('/api/recognize', methods=['POST'])
@token_required
def recognize(user_id):
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_data = request.files['audio']
    recognized_text = recognize_speech(audio_data)
    return jsonify({'recognized_text': recognized_text}), 200


@app.route('/api/synthesize', methods=['POST'])
@token_required
def synthesize(user_id):
    text = request.json.get('text')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    audio = synthesize_speech(text)
    return jsonify({'audio': audio}), 200


@app.route('/api/synthesize-speech', methods=['OPTIONS'])
def options_synthesize_speech():
    """Endpoint para lidar com requisições OPTIONS para CORS"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    return response


@app.route('/api/synthesize-speech', methods=['POST'])
def synthesize_speech_endpoint():
    """
    Endpoint para sintetizar fala usando Amazon Polly
    """
    try:
        print("Processando solicitação de síntese de fala")
        data = request.get_json()

        if not data or 'text' not in data:
            print("❌ Erro: Texto para síntese não fornecido")
            return jsonify({'success': False, 'error': 'No text provided'}), 400

        text = data.get('text')
        voice_settings = data.get('voice_settings', {})

        # Log da solicitação para debug
        print(f"📝 Texto para síntese: '{text}'")
        print(f"🔊 Configurações de voz: {voice_settings}")

        # Usar a função de síntese do módulo speech passando as configurações de voz diretamente
        audio_data = synthesize_speech(text, voice_settings)

        if not audio_data:
            print("❌ Erro: Falha ao gerar áudio")
            return jsonify({'success': False, 'error': 'Failed to synthesize speech'}), 500

        print("✅ Áudio sintetizado com sucesso.")

        # Retornar o áudio codificado em base64
        return jsonify({
            'success': True,
            'audio_data': audio_data
        }), 200
    except Exception as e:
        print(f"❌ Erro na síntese de fala: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Speech synthesis error: {str(e)}'}), 500


@app.route('/api/evaluate-pronunciation', methods=['POST'])
@token_required
def evaluate_pronunciation(user_id):
    global mcp_coordinator  # Certifique-se que o coordenador global está acessível

    try:
        # 1. Validar request
        if 'audio' not in request.files:
            print("❌ Error: No audio file in request")
            return jsonify({
                "success": False,
                "message": "No audio file provided",
                "error_code": "NO_AUDIO"
            }), 400

        audio_file = request.files['audio']
        expected_word = request.form.get('expected_word')

        if not expected_word or expected_word.strip() == '':
            print("❌ Error: No expected word provided")
            return jsonify({
                "success": False,
                "message": "Expected word not provided",
                "error_code": "NO_EXPECTED_WORD"
            }), 400

        # Log da chamada
        print(f"Routing pronunciation evaluation to MCP Coordinator:")
        print(
            f"- Audio file: {audio_file.filename} ({audio_file.content_type})")
        print(f"- Expected word: '{expected_word}'")
        print(f"- User ID: {user_id}")

        # 2. Chamar o MCP Coordinator para fazer a avaliação
        # Certifique-se que mcp_coordinator está inicializado (deve estar pelo @app.before_request)
        if not mcp_coordinator:
            print("❌ Error: MCP Coordinator not initialized!")
            return jsonify({
                "success": False,
                "message": "Internal server error: Coordinator not available",
                "error_code": "COORDINATOR_UNAVAILABLE"
            }), 500

        evaluation_result = mcp_coordinator.evaluate_pronunciation(
            user_id=user_id,
            audio_file_storage=audio_file,
            expected_word=expected_word
        )

        status_code = 200 if evaluation_result.get("success", False) else 500
        if not evaluation_result.get("success", False) and status_code == 500:
            print(
                f"❌ Evaluation failed within coordinator: {evaluation_result.get('message')}")

        # --- NOVO: Mascarar antes de imprimir na rota ---
        log_result_route = evaluation_result.copy()
        audio_key = "audio_feedback"
        if audio_key in log_result_route and isinstance(log_result_route[audio_key], str) and len(log_result_route[audio_key]) > 100:
            log_result_route[audio_key] = f"<{audio_key} len={len(log_result_route[audio_key])}>"
        print(
            f"✓ Evaluation result from coordinator (Route Log): {log_result_route}")
        # --- FIM DA MODIFICAÇÃO ---

        # Retorna o resultado ORIGINAL completo para o frontend
        return jsonify(evaluation_result), status_code

    except Exception as e:
        # Captura exceções que podem ocorrer *antes* da chamada ao coordenador
        print(f"❌ Top-level pronunciation evaluation error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Unexpected error in evaluation endpoint: {str(e)}",
            "error_code": "ENDPOINT_ERROR"
        }), 500


@app.route('/api/gigi/generate-game', methods=['OPTIONS'])
def options_gigi_game_generator():
    """Endpoint para lidar com requisições OPTIONS para CORS"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    return response


@app.route('/api/gigi/generate-game', methods=['POST'])
@token_required
def generate_gigi_game(user_id):
    try:
        print("Received request for Gigi game generation")
        print(f"User ID: {user_id}")

        data = request.get_json() or {}
        print(f"Request data: {data}")

        # Extract and validate parameters from request
        game_type = data.get('game_type', "exercícios de pronúncia")

        # Map difficulty values to ensure consistency
        difficulty_map = {
            'advanced': 'avançado',
            'medium': 'médio',
            'beginner': 'iniciante'
        }

        # Get difficulty from request and map it, default to 'iniciante'
        requested_difficulty = data.get('difficulty', 'beginner')
        difficulty = difficulty_map.get(
            requested_difficulty.lower(), 'iniciante')

        print(
            f"Mapped difficulty from '{requested_difficulty}' to '{difficulty}'")

        # Make sure the MCP coordinator is initialized
        global game_generator, mcp_coordinator
        if not game_generator or not mcp_coordinator:
            initialize_services()
            if not game_generator or not mcp_coordinator:
                return jsonify({
                    "success": False,
                    "message": "Não foi possível inicializar os serviços de jogo"
                }), 500

        # Use the game_designer to create a game with the correct difficulty
        try:
            game_data = mcp_coordinator.game_designer.create_game(
                user_id=user_id,
                difficulty=difficulty,
                game_type=game_type
            )

            # Save the generated game to database
            game_id = db.store_game(user_id, game_data)

            # Return the game data to the client
            return jsonify({
                "success": True,
                "game": {
                    "game_id": str(game_id),
                    "title": game_data.get("title", "Novo Jogo"),
                    "difficulty": difficulty,
                    "game_type": game_type,
                    "content": game_data.get("content", [])
                }
            })

        except Exception as game_error:
            print(f"Erro ao gerar jogo: {str(game_error)}")
            traceback.print_exc()

            # Fallback to game_generator
            game_data = game_generator.create_game(
                user_id=user_id,
                difficulty=difficulty,
                game_type=game_type
            )

            # Save the fallback game
            game_id = db.store_game(user_id, game_data)

            # Return the fallback game data
            return jsonify({
                "success": True,
                "game": {
                    "game_id": str(game_id),
                    "title": game_data.get("title", "Novo Jogo"),
                    "difficulty": difficulty,
                    "game_type": game_type,
                    "content": game_data.get("content", [])
                }
            })

    except Exception as e:
        print(f"Erro na geração do jogo pela Gigi: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Falha ao gerar jogo: {str(e)}"
        }), 500


@app.route('/api/games/<game_id>', methods=['GET', 'OPTIONS'])
def get_game_endpoint(game_id):
    """
    Endpoint para obter os detalhes de um jogo específico
    """
    # Tratar requisições OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response

    # Para requisições GET, verificamos a autenticação
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No authorization header provided'}), 401

    try:
        # Extrair e validar o token
        token = auth_header.split(" ")[1] if len(
            auth_header.split(" ")) > 1 else auth_header
        print(f"Token recebido: {token[:15]}...")
        print(f"Decodificando token com chave: {JWT_SECRET_KEY[:10]}...")
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = data.get('user_id')

        print(f"Token decodificado: {data}")
        print(f"User ID extraído do token: {user_id}")

        if not user_id:
            return jsonify({'error': 'Invalid token - no user_id'}), 401

        # Verificar se o usuário existe
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        print(f"✅ Usuário encontrado: {user.get('name', '')}")

    except Exception as e:
        print(f"❌ Erro na autenticação: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 401

    try:
        print(f"Buscando jogo com ID: {game_id} para usuário: {user_id}")

        # Buscar o jogo no banco de dados
        game = db.get_game(game_id)

        if not game:
            print(f"Jogo não encontrado: {game_id}")
            return jsonify({
                "success": False,
                "message": "Game not found"
            }), 404

        print(f"Jogo encontrado: {game.get('title', 'Sem título')}")

        # Obter o conteúdo que pode estar em diferentes formatos
        content = game.get("content", {})

        # Transformar os dados do jogo para garantir um formato consistente
        transformed_game = {
            "game_id": str(game.get("_id", game_id)),
            "title": content.get("title", game.get("title", "Game")),
            "description": content.get("description", game.get("description", "")),
            "instructions": content.get("instructions", game.get("instructions", [])),
            "difficulty": content.get("difficulty", game.get("difficulty", "iniciante")),
            "game_type": content.get("game_type", game.get("game_type", "exercícios de pronúncia")),
            "metadata": content.get("metadata", game.get("metadata", {}))
        }

        # Obter os exercícios e transformá-los no formato esperado pelo frontend
        exercises = []

        # Verificar diferentes possíveis localizações para os exercícios
        if isinstance(content, dict) and "exercises" in content:
            raw_exercises = content.get("exercises", [])
        elif isinstance(content, dict) and "content" in content:
            raw_exercises = content.get("content", [])
        elif "exercises" in game:
            raw_exercises = game.get("exercises", [])
        elif "content" in game and isinstance(game.get("content"), list):
            raw_exercises = game.get("content", [])
        elif isinstance(content, list):
            # Às vezes o content em si pode ser a lista de exercícios
            raw_exercises = content
        else:
            raw_exercises = []

        print(f"Encontrados {len(raw_exercises)} exercícios")

        # Transformar os exercícios em um formato consistente
        for idx, exercise in enumerate(raw_exercises):
            if not isinstance(exercise, dict):
                print(f"Pulando exercício não-dict: {exercise}")
                continue

            transformed_exercise = {
                "word": exercise.get("word", exercise.get("text", exercise.get("answer", exercise.get("starter", "")))),
                "prompt": exercise.get("prompt", exercise.get("tip", exercise.get("clue", "Pronuncie esta palavra"))),
                "hint": exercise.get("hint", exercise.get("tip", "Fale devagar")),
                "visual_cue": exercise.get("visual_cue", exercise.get("word", "")),
                "index": idx,
                "total": len(raw_exercises)
            }
            exercises.append(transformed_exercise)

        # Adicionar os exercícios transformados ao jogo
        transformed_game["content"] = exercises

        # Retornar os dados do jogo
        return jsonify({
            "success": True,
            "game": transformed_game
        })
    except Exception as e:
        print(f"Erro ao buscar jogo: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Error fetching game: {str(e)}"
        }), 500


@app.route('/api/game/finish', methods=['OPTIONS'])
def options_game_finish():
    """Endpoint para lidar com requisições OPTIONS para CORS"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    return response


@app.route('/api/game/finish', methods=['POST'])
@token_required
def finish_game(user_id):
    """
    Finaliza um jogo e atualiza o status no banco de dados
    """
    try:
        # Log detalhado para depuração
        print(f"========== FINALIZANDO JOGO ==========")

        # Extrair dados do request
        data = request.json
        session_id = data.get('session_id')
        completed_manually = data.get('completed_manually', False)
        completion_option = data.get('completion_option', 'finish')
        final_score = data.get('final_score', 0)
        generate_next = data.get('generate_next', False)

        print(
            f"Dados recebidos: session_id={session_id}, score={final_score}, option={completion_option}")

        if not session_id:
            print("❌ Erro: ID da sessão não fornecido")
            return jsonify({
                "success": False,
                "message": "ID da sessão não fornecido"
            }), 400

        # Buscar a sessão no banco de dados
        session = db.get_session(session_id)
        print(f"Sessão encontrada: {session is not None}")

        if not session:
            print(f"❌ Erro: Sessão não encontrada com ID: {session_id}")
            return jsonify({
                "success": False,
                "message": "Sessão não encontrada"
            }), 404

        # Verificar se o usuário tem permissão para finalizar esta sessão
        session_user_id = session.get('user_id')
        print(
            f"User ID da sessão: {session_user_id}, User ID autenticado: {user_id}")

        if str(session_user_id) != str(user_id):
            print(
                f"❌ Erro: Usuário {user_id} não tem permissão para finalizar a sessão de {session_user_id}")
            return jsonify({
                "success": False,
                "message": "Você não tem permissão para finalizar esta sessão"
            }), 403

        # Capturar o game_id da sessão para atualizar o jogo
        game_id = session.get('game_id')
        print(f"Game ID associado à sessão: {game_id}")

        # Atualizar os dados da sessão com os valores enviados pelo frontend
        update_data = {
            'completed': True,
            'end_time': datetime.datetime.now().isoformat(),
            'completed_manually': completed_manually,
            'completion_option': completion_option,
            'final_score': final_score,
            'exercises_completed': len(session.get('exercises', [])) if 'exercises' in session else 0
        }

        print(f"Atualizando sessão com dados: {update_data}")

        # Atualizar a sessão no banco de dados
        success = db.update_session(session_id, update_data)
        print(f"Atualização da sessão: {'Sucesso' if success else 'Falha'}")

        # Se o jogo foi identificado, também atualize seu status para 'completed'
        if game_id:
            try:
                print(f"Atualizando status do jogo {game_id} para 'completed'")
                # Atualizar o jogo no banco de dados
                game_update_result = db.update_game(game_id, {
                    'completed': True,
                    'completed_at': datetime.datetime.now().isoformat(),
                    'final_score': final_score
                })
                print(
                    f"Atualização do jogo: {'Sucesso' if game_update_result else 'Falha'}")
            except Exception as game_err:
                print(f"❌ Erro ao atualizar jogo: {str(game_err)}")
                # Não bloquear o fluxo se houver erro na atualização do jogo

        if not success:
            print("❌ Erro: Falha ao atualizar a sessão no banco de dados")
            return jsonify({
                "success": False,
                "message": "Falha ao atualizar a sessão"
            }), 500

        # Atualizar as estatísticas do usuário
        user = db.get_user_by_id(user_id)
        if user:
            print(
                f"Atualizando estatísticas do usuário: {user.get('name', 'Unknown')}")

            # Determinar o número de exercícios concluídos
            if 'exercises' in session:
                exercises_completed = len(session['exercises'])
            else:
                exercises_completed = update_data.get('exercises_completed', 0)

            # Atualizar contador total de exercícios
            current_exercises = user.get(
                'statistics', {}).get('exercises_completed', 0)

            # Calcular nova precisão média
            current_accuracy = user.get('statistics', {}).get('accuracy', 0)
            completed_sessions_count = len(
                user.get('history', {}).get('completed_sessions', [])) + 1

            # Evitar divisão por zero
            if completed_sessions_count > 0:
                new_accuracy = ((current_accuracy * (completed_sessions_count - 1)
                                 ) + final_score) / completed_sessions_count
            else:
                new_accuracy = final_score

            # Preparar dados de atualização
            user_updates = {
                'statistics.exercises_completed': current_exercises + exercises_completed,
                'statistics.last_activity': datetime.datetime.now().isoformat(),
                'statistics.accuracy': round(new_accuracy, 2)
            }

            # Adicionar resumo da sessão ao histórico
            session_summary = {
                'session_id': session_id,
                'completed_at': datetime.datetime.now().isoformat(),
                'difficulty': session.get('difficulty', 'iniciante'),
                'score': final_score,
                'exercises_completed': exercises_completed,
                'game_id': game_id,
                'game_title': session.get('game_title', 'Jogo sem título')
            }

            # Atualizar dados do usuário no banco de dados
            try:
                db.update_user(user_id, user_updates)

                # Adicionar sessão ao histórico
                history_update = db.add_to_user_history(
                    user_id, session_summary)
                print(
                    f"Atualização do histórico: {'Sucesso' if history_update else 'Falha'}")
            except Exception as user_err:
                print(
                    f"❌ Erro ao atualizar estatísticas do usuário: {str(user_err)}")
                # Continuar mesmo se houver erro na atualização do usuário

        # Se solicitado, gerar um novo jogo
        next_game = None
        if generate_next:
            try:
                # Usar a mesma dificuldade do jogo atual ou um nível acima dependendo da pontuação
                current_difficulty = session.get('difficulty', 'iniciante')
                difficulty_map = {
                    'iniciante': 'médio' if final_score > 90 else 'iniciante',
                    'médio': 'avançado' if final_score > 90 else 'médio',
                    'avançado': 'avançado'
                }
                next_difficulty = difficulty_map.get(
                    current_difficulty, 'iniciante')

                # Gerar próximo jogo usando Gigi
                next_game_data = game_generator.create_game(
                    user_id=user_id,
                    difficulty=next_difficulty,
                    game_type="exercícios de pronúncia"
                )

                # Processar e salvar o próximo jogo
                if next_game_data:
                    next_game_id = db.store_game(user_id, next_game_data)
                    next_game = {
                        "game_id": str(next_game_id),
                        "title": next_game_data.get("title", "Próximo Jogo"),
                        "difficulty": next_difficulty
                    }
            except Exception as next_game_err:
                print(f"❌ Erro ao gerar próximo jogo: {str(next_game_err)}")
                # Continuar mesmo sem gerar o próximo jogo

        response_data = {
            "success": True,
            "message": "Jogo finalizado com sucesso",
            "final_score": final_score
        }

        # Adicionar o próximo jogo à resposta se foi gerado
        if next_game:
            response_data["next_game"] = next_game

        print("========== JOGO FINALIZADO COM SUCESSO ==========")
        return jsonify(response_data)

    except Exception as e:
        print(f"❌ Erro ao finalizar jogo: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Erro interno ao finalizar o jogo: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')