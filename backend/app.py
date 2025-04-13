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

        # Se um game_id for fornecido, tentar buscar o jogo na base de dados
        game_data = None
        if game_id:
            try:
                game_data = db.get_game(game_id)
                print(
                    f"Jogo encontrado: {game_data.get('title') if game_data else 'Não encontrado'}")
            except Exception as e:
                print(f"Erro ao buscar jogo {game_id}: {str(e)}")
                # Continuar mesmo se o jogo não for encontrado

        # Criar uma nova sessão de jogo usando MCP
        session_data = mcp_coordinator.create_game_session(
            user_id, user_profile)

        # Associar a sessão com o jogo que está sendo jogado
        if game_id:
            session_data["game_id"] = game_id
            session_data["game_title"] = title
            session_data["game_type"] = game_type

        # Adicionar ID de sessão para rastreamento
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
                "word": current_exercise.get("word", ""),
                "prompt": current_exercise.get("prompt", "Pronuncie esta palavra"),
                "hint": current_exercise.get("hint", "Fale devagar"),
                "visual_cue": current_exercise.get("visual_cue", "Uma imagem apareceria aqui"),
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


@app.route('/api/lipsync/phoneme', methods=['GET'])
@token_required
def get_phoneme_viseme(user_id):
    """Retorna dados de visema para um fonema específico"""
    try:
        phoneme = request.args.get('phoneme')
        if not phoneme:
            return jsonify({"success": False, "message": "Fonema não especificado"}), 400

        # Gerar áudio do fonema
        audio_data = None
        audio_file = None

        try:
            # Gerar uma palavra de exemplo contendo o fonema
            example_word = get_example_word_for_phoneme(phoneme)

            # Tentar sintetizar fala
            audio_data = synthesize_speech(example_word)

            if audio_data:
                # Salvar em arquivo temporário
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_data)
                    audio_file = temp_file.name
        except Exception as e:
            print(f"Aviso: Não foi possível gerar áudio para o fonema: {e}")

        # Obter dados de sincronização labial
        viseme = lipsync_generator.generate_lipsync_for_phoneme(
            phoneme, audio_file)

        # Limpar arquivo temporário
        if audio_file and os.path.exists(audio_file):
            os.unlink(audio_file)

        return jsonify({
            "success": True,
            "phoneme": phoneme,
            "viseme": viseme
        }), 200
    except Exception as e:
        print(f"Erro ao gerar visema para fonema: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/lipsync/word', methods=['POST'])
@token_required
def generate_word_lipsync(user_id):
    """Gera dados de lipsync para uma palavra"""
    try:
        data = request.json
        word = data.get('word')

        if not word:
            return jsonify({"success": False, "message": "Palavra não especificada"}), 400

        # Gerar áudio da palavra
        audio_data = synthesize_speech(word)
        if not audio_data:
            return jsonify({"success": False, "message": "Falha ao sintetizar áudio"}), 500

        # Salvar áudio em arquivo temporário
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            audio_file = temp_file.name

        # Gerar lipsync
        lipsync_data = lipsync_generator.generate_lipsync(
            audio_file, text=word)

        # Limpar arquivo temporário
        os.unlink(audio_file)

        if not lipsync_data:
            return jsonify({"success": False, "message": "Falha ao gerar lipsync"}), 500

        # Codificar áudio em base64 para enviar ao frontend
        import base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        return jsonify({
            "success": True,
            "word": word,
            "lipsyncData": lipsync_data,
            "audioData": audio_base64
        }), 200
    except Exception as e:
        print(f"Erro ao gerar lipsync para palavra: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# User sessions and reports


@app.route('/api/user/sessions', methods=['GET'])
@token_required
def get_user_sessions(user_id):
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sessions = db.get_user_sessions(user_id, limit, offset)

    # Format the sessions for response
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            "session_id": session.get("_id", ""),
            "date": session.get("created_at", "").isoformat() if isinstance(session.get("created_at"), datetime.datetime) else session.get("created_at", ""),
            "difficulty": session.get("difficulty", "beginner"),
            "completed": session.get("completed", False),
            "score": session.get("final_score", 0),
            "exercises_completed": session.get("current_index", 0),
            "total_exercises": len(session.get("exercises", []))
        })

    return jsonify({"sessions": sessions_data}), 200


@app.route('/api/user/reports', methods=['GET'])
@token_required
def get_user_reports(user_id):
    # Get user data
    user = db.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get completed sessions
    completed_sessions = user.get("history", {}).get("completed_sessions", [])

    # Calculate progress statistics
    total_sessions = len(completed_sessions)
    if total_sessions == 0:
        return jsonify({
            "total_sessions": 0,
            "average_score": 0,
            "progress": [],
            "word_accuracy": {},
            "difficulty_distribution": {}
        }), 200

    # Calculate average score from completed sessions
    average_score = sum(session.get("score", 0)
                        for session in completed_sessions) / total_sessions

    # Get the last 10 sessions for progress chart
    sorted_sessions = sorted(completed_sessions, key=lambda x: x.get(
        "completed_at", ""), reverse=True)
    recent_sessions = sorted_sessions[:10]
    recent_sessions.reverse()  # Put in chronological order

    progress = [
        {
            "date": session.get("completed_at", ""),
            "score": session.get("score", 0),
            "difficulty": session.get("difficulty", "beginner")
        }
        for session in recent_sessions
    ]

    # Get word accuracy from evaluations
    evaluations = db.get_user_evaluations(
        user_id, 100)  # Get recent evaluations
    word_accuracy = {}

    for eval in evaluations:
        word = eval.get("expected_word", "").lower()
        if word:
            if word not in word_accuracy:
                word_accuracy[word] = {"total": 0, "correct": 0}

            word_accuracy[word]["total"] += 1
            # Assume correct if accuracy score is above 70%
            if eval.get("accuracy_score", 0) >= 0.7:
                word_accuracy[word]["correct"] += 1

    # Calculate percentages
    for word in word_accuracy:
        if word_accuracy[word]["total"] > 0:
            word_accuracy[word]["percentage"] = (
                word_accuracy[word]["correct"] / word_accuracy[word]["total"]) * 100
        else:
            word_accuracy[word]["percentage"] = 0

    # Get difficulty distribution
    difficulty_count = {"beginner": 0, "intermediate": 0, "advanced": 0}
    for session in completed_sessions:
        difficulty = session.get("difficulty", "beginner")
        difficulty_count[difficulty] = difficulty_count.get(difficulty, 0) + 1

    difficulty_distribution = {
        difficulty: (count / total_sessions) * 100
        for difficulty, count in difficulty_count.items()
    }

    # Return complete report data
    return jsonify({
        "total_sessions": total_sessions,
        "average_score": average_score,
        "progress": progress,
        "word_accuracy": word_accuracy,
        "difficulty_distribution": difficulty_distribution
    }), 200

# Rotas para exercícios


@app.route('/api/exercises', methods=['GET'])
@token_required
def get_exercises(user_id):
    """Obter todos os exercícios disponíveis para o usuário"""
    try:
        # Em uma implementação real, você buscaria exercícios personalizados
        # com base no nível do usuário e progressão
        exercises = [
            {
                "id": 1,
                "title": "Pronunciação de R",
                "difficulty": "beginner",
                "description": "Pratique palavras com som de R inicial"
            },
            {
                "id": 2,
                "title": "Sons de S e Z",
                "difficulty": "intermediate",
                "description": "Diferencie sons sibilantes em palavras comuns"
            },
            {
                "id": 3,
                "title": "Frases Complexas",
                "difficulty": "advanced",
                "description": "Pratique frases com múltiplos sons desafiadores"
            }
        ]
        return jsonify({"success": True, "exercises": exercises}), 200
    except Exception as e:
        print(f"Erro ao buscar exercícios: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao buscar exercícios"}), 500


@app.route('/api/exercises/<exercise_id>', methods=['GET'])
@token_required
def get_exercise(exercise_id, user_id):
    """Obter detalhes de um exercício específico"""
    try:
        # Em uma implementação real, você buscaria o exercício do banco de dados
        # E verificaria se o usuário tem acesso a ele

        # Exemplos de dados para diferentes exercícios
        exercises_data = {
            "1": {
                "id": 1,
                "title": "Pronunciação de R",
                "difficulty": "beginner",
                "description": "Pratique a pronúncia do som 'R' no início das palavras.",
                "instructions": "Clique em 'Iniciar' e pronuncie a palavra mostrada claramente.",
                "words": [
                    {"id": 1, "text": "rato", "hint": "Um animal pequeno que rói"},
                    {"id": 2, "text": "rosa", "hint": "Uma flor bonita"},
                    {"id": 3, "text": "rio", "hint": "Água que corre"},
                    {"id": 4, "text": "roda", "hint": "Parte de um carro"},
                    {"id": 5, "text": "rua", "hint": "Onde ficam as casas"}
                ]
            },
            "2": {
                "id": 2,
                "title": "Sons de S e Z",
                "difficulty": "intermediate",
                "description": "Diferencie sons sibilantes em palavras comuns.",
                "instructions": "Pronuncie cuidadosamente cada palavra, focando nos sons de S e Z.",
                "words": [
                    {"id": 1, "text": "casa", "hint": "Onde moramos"},
                    {"id": 2, "text": "zero", "hint": "Número antes do um"},
                    {"id": 3, "text": "sapo", "hint": "Animal que pula"},
                    {"id": 4, "text": "asa", "hint": "Parte de um pássaro"},
                    {"id": 5, "text": "zona", "hint": "Área ou região"}
                ]
            },
            "3": {
                "id": 3,
                "title": "Frases Complexas",
                "difficulty": "advanced",
                "description": "Pratique frases com múltiplos sons desafiadores.",
                "instructions": "Leia cada frase completa tentando manter uma pronúncia clara e fluente.",
                "words": [
                    {"id": 1, "text": "O rato roeu a roupa do rei de Roma",
                        "hint": "Trava-língua famoso"},
                    {"id": 2, "text": "Três tigres tristes",
                        "hint": "Sobre felinos melancólicos"},
                    {"id": 3, "text": "A aranha arranha a jarra",
                        "hint": "Sobre um inseto"},
                    {"id": 4, "text": "Pedro pregou um prego",
                        "hint": "Alguém fazendo uma tarefa"},
                    {"id": 5, "text": "A Zazá não está na casa da Zezé",
                        "hint": "Sobre a localização de alguém"}
                ]
            }
        }

        exercise = exercises_data.get(str(exercise_id))
        if not exercise:
            return jsonify({"success": False, "message": "Exercício não encontrado"}), 404

        return jsonify({"success": True, "exercise": exercise}), 200
    except Exception as e:
        print(f"Erro ao buscar exercício: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao buscar exercício"}), 500


@app.route('/api/exercise_results', methods=['POST'])
@token_required
def save_exercise_results(user_id):
    """Salvar resultados de um exercício completado"""
    try:
        data = request.json
        exercise_id = data.get('exerciseId')
        score = data.get('score')
        completed_words = data.get('completedWords')

        if not all([exercise_id, score is not None, completed_words is not None]):
            return jsonify({"success": False, "message": "Dados incompletos"}), 400

        # Em uma implementação real, você salvaria no banco de dados
        # result_id = db.save_exercise_result(user_id, exercise_id, score, completed_words)

        print(
            f"Salvando resultado para usuário {user_id}: Exercício {exercise_id}, Pontuação {score}")

        # Atualizar estatísticas do usuário seria feito aqui

        return jsonify({
            "success": True,
            "message": "Resultado salvo com sucesso",
            # "result_id": result_id
        }), 200
    except Exception as e:
        print(f"Erro ao salvar resultado: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# Adicione este endpoint:


@app.route('/api/log/stt', methods=['POST'])
@token_required
def log_stt_event(user_id):
    """Registra eventos de reconhecimento de fala do frontend"""
    try:
        data = request.json

        exercise_id = data.get('exerciseId')
        word = data.get('word')
        transcript = data.get('transcript')
        success = data.get('success')

        # Registrar o evento
        try:
            from utils.logger import ai_logger
            ai_logger.log_stt_event(
                user_id, exercise_id, word, transcript, success)
        except Exception as log_error:
            # Não falhar completamente se os logs tiverem problema
            print(f"AVISO: Erro ao registrar log: {log_error}")
            print(
                f"STT Event: User {user_id}, Word: {word}, Transcript: {transcript}, Success: {success}")

        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Erro ao processar evento STT: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/games/generate', methods=['POST'])
@token_required
def generate_game():
    try:
        user_id = g.user_id
        data = request.get_json()

        # Extract parameters from request
        difficulty = data.get('difficulty')
        game_type = data.get('game_type')

        # Generate game
        game_data = game_generator.create_game(
            user_id=user_id,
            difficulty=difficulty,
            game_type=game_type
        )

        # Store game in database
        game_id = db.store_game(user_id, game_data)

        # Return the game data
        return jsonify({
            "success": True,
            "game": game_data
        })
    except Exception as e:
        print(f"Game generation error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to generate game: {str(e)}"
        }), 500

# Add this route to use Gigi to generate games


@app.route('/api/game/next', methods=['POST', 'OPTIONS'])
@token_required
def generate_next_game(user_id):
    """Gera um novo jogo após o término do atual"""
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        print(f"Gerando próximo jogo para usuário: {user_id}")
        data = request.get_json() or {}

        # Extrair parâmetros da requisição
        difficulty = data.get('difficulty', 'iniciante')
        previous_game_id = data.get('previous_game_id')

        # Se um ID de jogo anterior foi fornecido, buscar sua dificuldade
        if previous_game_id:
            try:
                previous_game = db.get_game(previous_game_id)
                if previous_game:
                    difficulty = previous_game.get('difficulty', difficulty)
                    print(
                        f"Usando dificuldade do jogo anterior: {difficulty}")
            except Exception as e:
                print(f"Erro ao buscar jogo anterior: {str(e)}")

        # Sempre usar 'exercícios de pronúncia' como tipo
        game_type = "exercícios de pronúncia"

        # Verificar se o MCP coordinator está inicializado
        global mcp_coordinator
        if not mcp_coordinator:
            initialize_services()
            if not mcp_coordinator:
                return jsonify({
                    "success": False,
                    "message": "Não foi possível inicializar os serviços de jogo"
                }), 500

        # Usar o game_designer para criar um novo jogo
        game_data = mcp_coordinator.game_designer.create_game(
            user_id=user_id,
            difficulty=difficulty,
            game_type=game_type
        )

        # Transformar para o formato esperado pelo frontend
        exercises = []
        raw_exercises = game_data.get("content", [])

        for idx, exercise in enumerate(raw_exercises):
            transformed_exercise = {
                "word": exercise.get("word", ""),
                "prompt": exercise.get("tip", "Pronuncie esta palavra"),
                "hint": exercise.get("tip", "Fale devagar"),
                "visual_cue": exercise.get("word", ""),
                "index": idx,
                "total": len(raw_exercises)
            }
            exercises.append(transformed_exercise)

        # Criar o objeto de jogo compatível
        compatible_game = {
            "game_id": game_data.get("game_id", ""),
            "title": game_data.get("title", "Jogo de Pronúncia"),
            "description": game_data.get("description", ""),
            "instructions": game_data.get("instructions", []),
            "difficulty": game_data.get("difficulty", "iniciante"),
            "game_type": "exercícios de pronúncia",
            "content": exercises,
            "metadata": game_data.get("metadata", {})
        }

        # Salvar o jogo no banco de dados
        try:
            game_id = db.store_game(user_id, compatible_game)
            compatible_game["game_id"] = str(game_id)
        except Exception as e:
            print(
                f"Aviso: Não foi possível salvar o jogo no banco de dados: {str(e)}")

        return jsonify({
            "success": True,
            "game": compatible_game,
            "message": "Novo jogo gerado com sucesso"
        })

    except Exception as e:
        print(f"Erro ao gerar próximo jogo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Falha ao gerar próximo jogo: {str(e)}"
        }), 500


@app.route('/api/gigi/generate-game', methods=['POST'])
@token_required
def generate_gigi_game(user_id):
    try:
        print("Received request for Gigi game generation")
        print(f"User ID: {user_id}")

        data = request.get_json() or {}
        print(f"Request data: {data}")

        # Extract parameters from request
        difficulty = data.get('difficulty', 'iniciante')

        # Always use 'exercícios de pronúncia' type to ensure compatibility
        game_type = "exercícios de pronúncia"

        # Make sure the MCP coordinator is initialized
        global mcp_coordinator
        if not mcp_coordinator:
            initialize_services()
            if not mcp_coordinator:
                return jsonify({
                    "success": False,
                    "message": "Could not initialize game services"
                }), 500

        # Use the game_designer to create a game
        game_data = mcp_coordinator.game_designer.create_game(
            user_id=user_id,
            difficulty=difficulty,
            game_type=game_type
        )

        # Ensure the game structure is compatible with GameScreen.js
        exercises = []
        raw_exercises = game_data.get("content", [])

        for idx, exercise in enumerate(raw_exercises):
            # Transform each exercise to match what GameScreen expects
            transformed_exercise = {
                "word": exercise.get("word", ""),
                "prompt": exercise.get("tip", "Pronuncie esta palavra"),
                "hint": exercise.get("tip", "Fale devagar"),
                "visual_cue": exercise.get("word", ""),
                "index": idx,
                "total": len(raw_exercises)
            }
            exercises.append(transformed_exercise)

        # Create the final game object
        compatible_game = {
            "game_id": game_data.get("game_id", ""),
            "title": game_data.get("title", "Jogo de Pronúncia"),
            "description": game_data.get("description", ""),
            "instructions": game_data.get("instructions", []),
            "difficulty": game_data.get("difficulty", "iniciante"),
            "game_type": "exercícios de pronúncia",
            "content": exercises,
            "metadata": game_data.get("metadata", {})
        }

        # Store the game in the database
        try:
            game_id = db.store_game(user_id, compatible_game)
            compatible_game["game_id"] = str(game_id)
        except Exception as e:
            print(f"Warning: Could not store game in database: {str(e)}")

        return jsonify({
            "success": True,
            "game": compatible_game
        })

    except Exception as e:
        print(f"Gigi game generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Falha ao gerar jogo: {str(e)}"
        }), 500

# Adicione esta rota para lidar explicitamente com OPTIONS requests


@app.route('/api/gigi/generate-game', methods=['OPTIONS'])
def options_gigi_generate_game():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# Add this route to use MCP to create personalized sessions


@app.route('/api/mcp/create-session', methods=['POST'])
@token_required
def create_mcp_session():
    try:
        user_id = g.user_id
        data = request.get_json()
        user_profile = data.get('user_profile', {})
        focus_areas = data.get('focus_areas', [])

        # Initialize MCP if not already done
        global mcp_coordinator
        if not mcp_coordinator:
            mcp_coordinator = MCPCoordinator(db.client, OPENAI_API_KEY)

        # Get more comprehensive user profile from database if needed
        if not user_profile or len(user_profile) == 0:
            user_profile = db.get_user_profile(user_id)

        # Add focus areas to user profile
        user_profile['focus_areas'] = focus_areas

        # Create a new session using MCP
        session = mcp_coordinator.create_game_session(user_id, user_profile)

        # Save session to database
        session_id = db.store_session(user_id, session)

        # Return session data
        return jsonify({
            "success": True,
            "session": session
        })
    except Exception as e:
        print(f"MCP session creation error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to create session: {str(e)}"
        }), 500


@app.route('/api/games/<game_id>', methods=['GET'])
@token_required
def get_game(game_id, user_id):
    try:
        print(f"Fetching game with ID: {game_id} for user: {user_id}")

        # Get game from database
        game = db.get_game(game_id)

        if not game:
            print(f"Game not found: {game_id}")
            return jsonify({
                "success": False,
                "message": "Game not found"
            }), 404

        print(f"Game found: {game.get('title', 'No title')}")

        # Get the content which might be in different formats
        content = game.get("content", {})

        # Transform game data to ensure it matches the expected format in GameScreen.js
        transformed_game = {
            "game_id": str(game.get("_id", game_id)),
            "title": content.get("title", game.get("title", "Game")),
            "description": content.get("description", game.get("description", "")),
            "instructions": content.get("instructions", game.get("instructions", [])),
            "difficulty": content.get("difficulty", game.get("difficulty", "iniciante")),
            "game_type": content.get("game_type", game.get("game_type", "exercícios de pronúncia")),
            "metadata": content.get("metadata", game.get("metadata", {}))
        }

        # Get the exercises and transform them into the format GameScreen.js expects
        exercises = []

        # Check different possible locations for exercises
        if isinstance(content, dict) and "exercises" in content:
            raw_exercises = content.get("exercises", [])
        elif isinstance(content, dict) and "content" in content:
            raw_exercises = content.get("content", [])
        elif "exercises" in game:
            raw_exercises = game.get("exercises", [])
        elif isinstance(content, list):
            # Sometimes content itself might be the list of exercises
            raw_exercises = content
        else:
            raw_exercises = []

        print(f"Found {len(raw_exercises)} exercises")

        # Add debugging to see raw exercise structure
        if raw_exercises and len(raw_exercises) > 0:
            print(f"First exercise sample: {raw_exercises[0]}")

        # Transform the exercises into a consistent format
        for idx, exercise in enumerate(raw_exercises):
            if not isinstance(exercise, dict):
                print(f"Skipping non-dict exercise: {exercise}")
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

        # Add the transformed exercises to the game
        transformed_game["content"] = exercises

        # Return the game data
        return jsonify({
            "success": True,
            "game": transformed_game
        })
    except Exception as e:
        print(f"Error fetching game: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Error fetching game: {str(e)}"
        }), 500


@app.route('/api/games/<game_id>', methods=['OPTIONS'])
def options_get_game(game_id):
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response

# Helper functions


def calculate_average_score(user):
    completed_sessions = user.get("history", {}).get("completed_sessions", [])
    if not completed_sessions:
        return 0

    return sum(session.get("score", 0) for session in completed_sessions) / len(completed_sessions)


@app.route('/api/evaluate-pronunciation', methods=['POST'])
@token_required
def evaluate_pronunciation(user_id):
    try:
        if 'audio' not in request.files:
            return jsonify({"success": False, "message": "Nenhum arquivo de áudio encontrado"}), 400

        audio_file = request.files['audio']
        expected_word = request.form.get('expected_word', '')

        if not expected_word:
            return jsonify({"success": False, "message": "Palavra esperada não fornecida"}), 400

        # Mostrar informações sobre o arquivo recebido para debug
        print(
            f"Arquivo de áudio recebido: {audio_file.filename}, tipo MIME: {audio_file.content_type}")
        print(f"Palavra esperada: '{expected_word}'")

        # 1. Salvar o arquivo de áudio temporariamente
        temp_path = f"/tmp/pronunciation_{user_id}_{int(time.time())}.webm"
        audio_file.save(temp_path)
        print(f"Arquivo de áudio salvo em: {temp_path}")

        # 2. Converter o arquivo WebM para WAV usando FFmpeg se disponível
        try:
            import subprocess
            wav_path = f"/tmp/pronunciation_{user_id}_{int(time.time())}.wav"
            result = subprocess.run([
                'ffmpeg', '-i', temp_path, '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1', wav_path
            ], capture_output=True)

            if result.returncode == 0:
                print(f"Arquivo convertido com sucesso para WAV: {wav_path}")
                recognized_text = recognize_speech(wav_path)
            else:
                print("Falha ao converter áudio. Tentando reconhecimento direto.")
                recognized_text = recognize_speech(temp_path)
        except Exception as e:
            print(f"Erro ao converter áudio: {e}")
            recognized_text = recognize_speech(temp_path)

        print(f"Texto reconhecido: '{recognized_text}'")
        print(
            f"Comparação: Esperado='{expected_word}' | Reconhecido='{recognized_text}'")

        # 3. Se o reconhecimento falhar, fornecer feedback genérico com voz
        if not recognized_text:
            print("AVISO: Texto não reconhecido pelo STT")
            feedback_message = "Não consegui entender o que disseste. Por favor, tenta novamente falando mais claramente."

            # Gerar áudio para o feedback
            feedback_audio = synthesize_speech(feedback_message)

            return jsonify({
                "success": True,
                "isCorrect": False,
                "score": 3,
                "recognized_text": "",
                "feedback": feedback_message,
                "audio_feedback": feedback_audio
            })

        # 4. Avaliar a pronúncia usando o speech evaluator
        from ai.agents.speech_evaluator_agent import SpeechEvaluatorAgent
        evaluator = SpeechEvaluatorAgent(OpenAI(api_key=OPENAI_API_KEY))

        print(
            f"Iniciando avaliação de pronúncia para: '{recognized_text}' (esperado: '{expected_word}')")
        evaluation = evaluator.evaluate_pronunciation(
            spoken_text=recognized_text,
            expected_word=expected_word,
            hint=f"Foca na pronúncia correta do som em '{expected_word}'"
        )

        # 5. Gerar feedback detalhado
        accuracy_score = evaluation.get("accuracy_score", 5)
        is_correct = accuracy_score >= 7  # Considerar correto se score >= 7
        matched_sounds = evaluation.get("matched_sounds", [])
        challenging_sounds = evaluation.get("challenging_sounds", [])
        detailed_feedback = evaluation.get("detailed_feedback", "")

        # 6. Gerar feedback em áudio
        audio_feedback = synthesize_speech(detailed_feedback)

        # 7. Limpar arquivos temporários
        try:
            os.remove(temp_path)
            if 'wav_path' in locals() and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception as e:
            print(f"Erro ao remover arquivos temporários: {e}")

        return jsonify({
            "success": True,
            "isCorrect": is_correct,
            "score": accuracy_score,
            "recognized_text": recognized_text,
            "matched_sounds": matched_sounds,
            "challenging_sounds": challenging_sounds,
            "feedback": detailed_feedback,
            "audio_feedback": audio_feedback
        })

    except Exception as e:
        print(f"Erro na avaliação de pronúncia: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500

# Função auxiliar para calcular a similaridade entre textos


def calculate_similarity(text1, text2):
    """Calcula a similaridade entre dois textos usando a distância de Levenshtein"""
    try:
        from rapidfuzz.distance import Levenshtein
        # Normalizar para pontuação entre 0 e 1
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 0
        distance = Levenshtein.distance(text1, text2)
        return max(0, 1 - (distance / max_len))
    except ImportError:
        # Fallback simples se rapidfuzz não estiver disponível
        if text1 == text2:
            return 1.0
        # Verificar se uma string está na outra
        if text1 in text2 or text2 in text1:
            shortest = min(len(text1), len(text2))
            longest = max(len(text1), len(text2))
            return shortest / longest
        # Verificar a correspondência simples de caracteres
        common_chars = sum(1 for c in text1 if c in text2)
        return common_chars / max(len(text1), len(text2))


@app.route('/api/user/current_progress', methods=['GET'])
@token_required
def get_current_progress(user_id):
    """Retorna o progresso atual do usuário em jogos ativos"""
    try:
        # Obter progresso em memória do GameDesigner
        if user_id in game_generator.current_games:
            current_game = game_generator.current_games[user_id]

            # Calcular percentual de conclusão
            total_exercises = len(current_game.get(
                "content", {}).get("exercises", []))
            current_index = current_game.get("current_index", 0)
            completion_percentage = (
                current_index / total_exercises * 100) if total_exercises > 0 else 0

            # Obter metadados para exibição
            return jsonify({
                "success": True,
                "has_active_game": True,
                "game_id": current_game.get("game_id"),
                "game_type": current_game.get("game_type"),
                "difficulty": current_game.get("difficulty"),
                "current_score": current_game.get("score", 0),
                "progress": {
                    "current_exercise": current_index,
                    "total_exercises": total_exercises,
                    "completion_percentage": round(completion_percentage, 1)
                },
                "started_at": current_game.get("created_at")
            })

        # Caso não tenha jogo ativo, buscar o histórico de progresso do banco de dados
        user = db.get_user(user_id)
        if user and "game_progress" in user and user["game_progress"]:
            # Pegar o progresso mais recente
            last_progress = user["game_progress"][0]

            return jsonify({
                "success": True,
                "has_active_game": False,
                "last_activity": {
                    "game_id": last_progress.get("game_id"),
                    "game_type": last_progress.get("game_type"),
                    "difficulty": last_progress.get("difficulty"),
                    "score": last_progress.get("current_score", 0),
                    "exercises_completed": last_progress.get("current_index", 0),
                    "timestamp": last_progress.get("timestamp")
                }
            })

        return jsonify({
            "success": True,
            "has_active_game": False,
            "message": "No active games or recent progress found"
        })

    except Exception as e:
        print(f"Error retrieving user progress: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to retrieve progress information"
        }), 500


@app.route('/api/user/statistics', methods=['GET'])
@token_required
def get_user_statistics(user_id):
    """Retorna estatísticas detalhadas do usuário para o dashboard"""
    try:
        # Obter usuário do banco de dados
        user = db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Obter estatísticas básicas
        stats = user.get("statistics", {})
        exercises_completed = stats.get("exercises_completed", 0)
        accuracy = stats.get("accuracy", 0)

        # Determinar nível atual e próximo nível
        difficulty_mapping = {
            "iniciante": {"next": "médio", "threshold": 80},
            "médio": {"next": "avançado", "threshold": 90},
            "avançado": {"next": "avançado+", "threshold": 100}
        }

        # Determinar nível atual com base na precisão média
        current_level = "iniciante"
        if accuracy >= 90:
            current_level = "avançado"
        elif accuracy >= 80:
            current_level = "médio"

        next_level = difficulty_mapping.get(
            current_level, {}).get("next", "médio")
        threshold = difficulty_mapping.get(
            current_level, {}).get("threshold", 80)

        # Calcular progresso para o próximo nível
        level_progress = 0
        if current_level == "iniciante":
            # 0-80% de precisão mapeia para 0-100% de progresso para nível médio
            level_progress = min(100, (accuracy / 80) * 100)
        elif current_level == "médio":
            # 80-90% de precisão mapeia para 0-100% de progresso para nível avançado
            level_progress = min(100, ((accuracy - 80) / 10) * 100)
        else:
            # No nível avançado, mantemos 100%
            level_progress = 100

        # Gerar mensagem personalizada
        level_message = ""
        if level_progress < 25:
            level_message = f"Continue praticando para melhorar sua precisão!"
        elif level_progress < 75:
            level_message = f"Você está progredindo bem para o nível {next_level}!"
        elif level_progress < 95:
            level_message = f"Você está quase pronto para avançar ao nível {next_level}!"
        else:
            level_message = f"Excelente! Você está dominando o nível {current_level}!"

        # Retornar estatísticas
        return jsonify({
            "exercises_completed": exercises_completed,
            "accuracy": accuracy,
            "current_level": current_level,
            "next_level": next_level,
            "level_progress_percentage": level_progress,
            "level_threshold": threshold,
            "level_progress_message": level_message,
            "last_login": stats.get("last_login", ""),
            "joined_days_ago": (datetime.datetime.utcnow() - user.get("created_at", datetime.datetime.utcnow())).days
        }), 200

    except Exception as e:
        print(f"Error retrieving user statistics: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve user statistics"
        }), 500


@app.route('/api/game/finish', methods=['OPTIONS'])
def options_finish_game():
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
                # Usar o método que adiciona o método update_game em db_connector.py
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
            new_accuracy = ((current_accuracy * (completed_sessions_count - 1)
                             ) + final_score) / completed_sessions_count

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
            db.update_user(user_id, user_updates)

            # Adicionar sessão ao histórico
            history_update = db.add_to_user_history(user_id, session_summary)
            print(
                f"Atualização do histórico: {'Sucesso' if history_update else 'Falha'}")

        # Se solicitado, gerar um novo jogo
        next_game = None
        if generate_next:
            # ... código existente para gerar próximo jogo ...
            pass

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
        import traceback
        print(f"❌ Erro ao finalizar jogo: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Erro interno ao finalizar o jogo: {str(e)}"
        }), 500


@app.route('/api/user/history', methods=['GET'])
@token_required
def get_user_history(user_id):
    """
    Retorna o histórico completo de sessões do usuário
    """
    try:
        # Buscar o usuário no banco de dados
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "Usuário não encontrado"
            }), 404

        # Extrair o histórico de sessões
        history = user.get("history", {})
        completed_sessions = history.get("completed_sessions", [])

        # Ordenar por data de conclusão (mais recente primeiro)
        sorted_sessions = sorted(
            completed_sessions,
            key=lambda x: x.get("completed_at", ""),
            reverse=True
        )

        # Preparar os dados para a resposta
        sessions_data = []
        for session in sorted_sessions:
            sessions_data.append({
                "session_id": session.get("session_id", ""),
                "game_id": session.get("game_id", ""),
                "game_title": session.get("game_title", "Jogo sem título"),
                "completed_at": session.get("completed_at", ""),
                "difficulty": session.get("difficulty", "iniciante"),
                "score": session.get("score", 0),
                "exercises_completed": session.get("exercises_completed", 0)
            })

        # Retornar dados de estatísticas gerais e sessões
        statistics = {
            "total_sessions": len(sessions_data),
            "average_score": sum(s.get("score", 0) for s in sessions_data) / max(len(sessions_data), 1),
            "total_exercises_completed": sum(s.get("exercises_completed", 0) for s in sessions_data),
            "sessions_by_difficulty": {
                "iniciante": len([s for s in sessions_data if s.get("difficulty") == "iniciante"]),
                "médio": len([s for s in sessions_data if s.get("difficulty") == "médio"]),
                "avançado": len([s for s in sessions_data if s.get("difficulty") == "avançado"])
            }
        }

        return jsonify({
            "success": True,
            "statistics": statistics,
            "sessions": sessions_data
        })

    except Exception as e:
        print(f"Erro ao buscar histórico do usuário: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Erro ao buscar histórico: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
