import os
import sys
import json
import datetime
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import logging
# Import app instance and JWT_SECRET_KEY from config
from config import DEBUG, OPENAI_API_KEY, app, JWT_SECRET_KEY
from bson import ObjectId
from flask.json import JSONEncoder
import tempfile
import base64
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
    global game_generator, mcp_coordinator

    # Verificar se já estão inicializados
    if game_generator is None or mcp_coordinator is None:
        try:
            # Inicializar game generator
            if game_generator is None:
                game_generator = GameGenerator()
                print("GameGenerator inicializado com sucesso")

            # Inicializar MCP coordinator
            if mcp_coordinator is None:
                openai_api_key = os.environ.get("OPENAI_API_KEY")
                if openai_api_key:
                    mcp_coordinator = MCPCoordinator(api_key=openai_api_key)
                    print("MCPCoordinator inicializado com sucesso")
                else:
                    print(
                        "Aviso: OPENAI_API_KEY não encontrada. Funcionalidades de IA serão limitadas.")
        except Exception as e:
            print(f"Error initializing services: {str(e)}")
            traceback.print_exc()


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
    # Get user profile from database
    user = db.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_profile = {
        "name": user.get('name', 'Friend'),
        "age": user.get('age', 6),
        "history": user.get('history', {})
    }

    # Create a new game session using MCP
    session_data = mcp_coordinator.create_game_session(user_id, user_profile)

    # Save session to database
    session_id = db.save_session(session_data)

    # Get first exercise
    current_exercise = session_data["exercises"][0]

    # Create response with welcome instructions and first exercise
    response = {
        "session_id": session_data["session_id"],
        "instructions": session_data["instructions"],
        "current_exercise": {
            "word": current_exercise["word"],
            "prompt": current_exercise["prompt"],
            "hint": current_exercise["hint"],
            "visual_cue": current_exercise.get("visual_cue", "A picture would appear here"),
            "index": 0,
            "total": len(session_data["exercises"])
        }
    }

    return jsonify(response), 200


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
    evaluation_results = mcp_coordinator.evaluate_response(
        session_data, recognized_text)

    # Update session in database with evaluation results
    if "evaluations" not in session_data:
        session_data["evaluations"] = []

    session_data["evaluations"].append({
        "exercise_index": session_data["current_index"],
        "expected_word": session_data["exercises"][session_data["current_index"]]["word"],
        "recognized_text": recognized_text,
        "accuracy_score": evaluation_results.get("accuracy_score", 0),
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

    # Update the current index if moving to the next exercise
    if evaluation_results["next_steps"]["advance_to_next"]:
        session_data["current_index"] += 1

    # Save evaluation as a separate record
    evaluation_record = {
        "session_id": session_id,
        "user_id": user_id,
        "exercise_index": session_data["current_index"],
        "expected_word": session_data["exercises"][session_data["current_index"]]["word"],
        "recognized_text": recognized_text,
        "evaluation": evaluation_results["evaluation"],
        "accuracy_score": evaluation_results.get("accuracy_score", 0)
    }
    db.save_evaluation(evaluation_record)

    # Update session in database
    db.update_session(session_id, session_data)

    # Prepare response with feedback and next exercise if applicable
    current_index = session_data["current_index"]
    total_exercises = len(session_data["exercises"])
    is_complete = current_index >= total_exercises

    if is_complete:
        # Calculate final score
        final_score = 0
        if session_data.get("evaluations"):
            scores = [ev.get("accuracy_score", 0)
                      for ev in session_data.get("evaluations")]
            final_score = int(sum(scores) / len(scores) * 100)

        # Update user history
        user = db.get_user(user_id)
        history = user.get("history", {})
        session_summary = {
            "completed_at": datetime.datetime.utcnow().isoformat(),
            "difficulty": session_data["difficulty"],
            "exercises_count": total_exercises,
            "score": final_score
        }
        if "completed_sessions" not in history:
            history["completed_sessions"] = []
        history["completed_sessions"].append(session_summary)
        db.update_user(user_id, {"history": history})

        # Mark session as completed
        db.update_session(
            session_id, {"completed": True, "final_score": final_score})

        response = {
            "session_complete": True,
            "feedback": evaluation_results["feedback"],
            "final_score": final_score
        }
    else:
        current_exercise = session_data["exercises"][current_index]
        response = {
            "session_complete": False,
            "feedback": evaluation_results["feedback"],
            "current_exercise": {
                "word": current_exercise["word"],
                "prompt": current_exercise["prompt"],
                "hint": current_exercise["hint"],
                "visual_cue": current_exercise.get("visual_cue", "A picture would appear here"),
                "index": current_index,
                "total": total_exercises
            },
            "repeat_exercise": not evaluation_results["next_steps"]["advance_to_next"]
        }

    return jsonify(response), 200


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
        if "exercises" in content:
            raw_exercises = content.get("exercises", [])
        else:
            raw_exercises = content.get("content", [])

        if not raw_exercises and "exercises" in game:
            raw_exercises = game.get("exercises", [])

        print(f"Found {len(raw_exercises)} exercises")

        # Transform the exercises into a consistent format
        for idx, exercise in enumerate(raw_exercises):
            transformed_exercise = {
                "word": exercise.get("word", exercise.get("answer", exercise.get("starter", ""))),
                "prompt": exercise.get("tip", exercise.get("clue", "Pronuncie esta palavra")),
                "hint": exercise.get("tip", "Fale devagar"),
                "visual_cue": exercise.get("word", ""),
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
        import traceback
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


if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
