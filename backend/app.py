from pathlib import Path
from routes.api import api_bp
import time
from gtts import gTTS
import io
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
import asyncio  # Add asyncio import
from asgiref.sync import async_to_sync  # Add this import
from functools import wraps  # Add this import
from functools import lru_cache  # Add lru_cache import
from ai.agents.speech_evaluator_agent import SpeechEvaluatorAgent
# Import app instance and JWT_SECRET_KEY from config
from config import DEBUG, OPENAI_API_KEY, app, JWT_SECRET_KEY
from bson import ObjectId
from flask.json import JSONEncoder
import jwt
from flask import Flask, request, jsonify, g, send_from_directory, Response
from flask_cors import CORS
from speech.recognition import recognize_speech
from speech.synthesis import synthesize_speech, get_example_word_for_phoneme
from speech.lipsync import LipsyncGenerator
from ai.server.mcp_coordinator import MCPSystem
# Import Message and ModelContext
from ai.server.mcp_server import Message, ModelContext
from ai.agents.game_designer_agent import GameDesignerAgent as GameGenerator
from auth.auth_service import AuthService
from auth.auth_middleware import token_required
from database.db_connector import DatabaseConnector
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importar o blueprint API

# Add project root to Python path
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    # Navigate up to speech-therapy-game
    project_root = current_dir.parent.parent.parent
    sys.path.insert(0, str(project_root))

# Add this decorator definition


def async_route(f):
    """Wrapper for async route handlers"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return async_to_sync(f)(*args, **kwargs)
    return wrapper

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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

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
            # Passar o db_connector para o MCPSystem (Change MCPCoordinator to MCPSystem)
            mcp_coordinator = MCPSystem(
                api_key=OPENAI_API_KEY, db_connector=db)
            # Changed Coordinator to System
            print("MCP System initialized with database connection")
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
@async_route
async def start_game(user_id):
    try:
        data = request.get_json()
        game_id = data.get('game_id')

        if not game_id:
            return jsonify({
                "success": False,
                "message": "No game_id provided"
            }), 400

        print(f"========== INICIANDO SESSÃO DE JOGO (Rota -> Coordenador) ==========")
        print(f"User ID: {user_id}")
        print(
            f"Dados recebidos: game_id={game_id}, título={data.get('title')}, dificuldade={data.get('difficulty')}")

        session_result = await mcp_coordinator.load_existing_game_session(user_id, game_id)

        # Log the response structure
        print(f"Response structure: {json.dumps(session_result, indent=2)}")

        if not session_result.get("success"):
            raise Exception(session_result.get(
                "error", "Unknown error loading game session"))

        return jsonify(session_result)

    except Exception as e:
        print(f"❌ Erro na rota /api/start_game: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Failed to start game: {str(e)}"
        }), 500


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


@app.route('/api/synthesize-speech', methods=['POST'])
def synthesize_speech_endpoint():
    """Endpoint para sintetizar fala a partir de texto"""
    try:
        print("Processando solicitação de síntese de fala")
        data = request.json

        if not data or 'text' not in data:
            print("❌ Dados de entrada inválidos")
            return jsonify({'success': False, 'error': 'Missing text parameter'}), 400

        text = data.get('text', '').strip()
        if not text:
            print("❌ Texto vazio")
            return jsonify({'success': False, 'error': 'Empty text'}), 400

        print(f"📝 Texto para síntese: '{text}'")

        # Usar gTTS diretamente aqui para evitar falhas na função externa
        from gtts import gTTS
        import io

        # Gerar áudio diretamente
        try:
            mp3_io = io.BytesIO()
            tts = gTTS(text=text, lang='pt', slow=False)
            tts.write_to_fp(mp3_io)
            mp3_io.seek(0)
            audio_bytes = mp3_io.read()

            # Verificar se o áudio foi gerado com sucesso
            if not audio_bytes or len(audio_bytes) < 100:
                print("❌ Falha ao gerar áudio - bytes insuficientes")
                return Response(
                    json.dumps(
                        {'success': False, 'error': 'Failed to generate audio'}),
                    mimetype='application/json',
                    status=500
                )

            # Codificar em base64 e converter para string
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            print(
                f"✅ Áudio gerado: {len(audio_bytes)} bytes, Base64: {len(audio_b64)} caracteres")

            # Criar resposta sem usar jsonify
            response_data = json.dumps(
                {'success': True, 'audio_data': audio_b64})
            return Response(
                response_data,
                mimetype='application/json',
                status=200
            )

        except Exception as e:
            print(f"❌ Erro interno de síntese: {str(e)}")
            traceback.print_exc()
            return Response(
                json.dumps(
                    {'success': False, 'error': f'Synthesis error: {str(e)}'}),
                mimetype='application/json',
                status=500
            )

    except Exception as e:
        print(f"❌ Erro geral no endpoint: {str(e)}")
        traceback.print_exc()
        return Response(
            json.dumps(
                {'success': False, 'error': f'General error: {str(e)}'}),
            mimetype='application/json',
            status=500
        )


@app.route('/api/tts-simple', methods=['POST', 'OPTIONS'])
def simple_tts_endpoint():
    """Endpoint simplificado para síntese de fala"""
    # Tratar requisições OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = Response('', 200)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.json
        if not data or 'text' not in data:
            return Response('{"success":false,"error":"Missing text parameter"}',
                            mimetype='application/json', status=400)

        text = data.get('text', '').strip()
        if not text:
            return Response('{"success":false,"error":"Empty text"}',
                            mimetype='application/json', status=400)

        print(f"Texto para TTS simples: '{text}'")

        # Usar gTTS
        from gtts import gTTS
        import io

        # Criar buffer e gerar áudio
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang='pt')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        # Codificar para base64
        audio_b64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
        print(f"TTS simples: Áudio gerado com {len(audio_b64)} caracteres")

        # Resposta direta sem usar jsonify
        return Response(
            '{"success":true,"audio_data":"' + audio_b64 + '"}',
            mimetype='application/json',
            status=200
        )

    except Exception as e:
        print(f"❌ Erro no TTS simples: {str(e)}")
        traceback.print_exc()
        return Response(
            '{"success":false,"error":"' + str(e).replace('"', '\\"') + '"}',
            mimetype='application/json',
            status=500
        )


@app.route('/api/evaluate-pronunciation', methods=['POST'])
@token_required
@async_route
async def evaluate_pronunciation(user_id):
    try:
        if 'audio' not in request.files:
            print("❌ Error: No audio file in request")
            return jsonify({
                "success": False,
                "message": "No audio file provided",
                "error_code": "NO_AUDIO"
            }), 400

        audio_file = request.files['audio']
        expected_word = request.form.get('expected_word')
        session_id = request.form.get('session_id')

        # Validação do expected_word
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
        if session_id:
            print(f"- Session ID: {session_id}")

        # Agora podemos usar await com a função assíncrona
        evaluation_result = await mcp_coordinator.evaluate_pronunciation(
            audio_file=audio_file,
            expected_word=expected_word,
            user_id=user_id,
            session_id=session_id
        )

        # Resto do código permanece igual...
        status_code = 200 if evaluation_result.get("success", False) else 500
        if not evaluation_result.get("success", False) and status_code == 500:
            print(
                f"❌ Evaluation failed within coordinator: {evaluation_result.get('message')}")

        # Mascaramento do log
        log_result_route = evaluation_result.copy()
        audio_key = "audio_feedback"
        if audio_key in log_result_route and isinstance(log_result_route[audio_key], str) and len(log_result_route[audio_key]) > 100:
            log_result_route[audio_key] = f"<{audio_key} len={len(log_result_route[audio_key])}>"
        print(
            f"✓ Evaluation result from coordinator (Route Log): {log_result_route}")
        return jsonify(evaluation_result), status_code

    except Exception as e:
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
@async_route
async def generate_gigi_game(user_id):
    try:
        print("Received request for Gigi game generation")
        print(f"User ID: {user_id}")

        data = request.get_json() or {}
        print(f"Request data: {data}")

        game_type = data.get('game_type', "exercícios de pronúncia")
        difficulty_map = {
            'advanced': 'avançado', 'medium': 'médio', 'beginner': 'iniciante'
        }
        requested_difficulty = data.get('difficulty', 'beginner')
        difficulty = difficulty_map.get(
            requested_difficulty.lower(), 'iniciante')
        print(
            f"Mapped difficulty from '{requested_difficulty}' to '{difficulty}'")

        global mcp_coordinator, db  # Ensure db is accessible
        if not mcp_coordinator:
            # initialize_services() # Likely called by before_request
            if not mcp_coordinator:
                print("❌ Error: MCP Coordinator not initialized after check!")
                return jsonify({
                    "success": False,
                    "message": "Não foi possível inicializar os serviços de jogo"
                }), 500

        # --- Corrected Code using MCP ---
        print("Creating message for game_designer agent...")
        context = ModelContext()  # Create a context for this interaction
        # Add user_id to context if needed by handlers/tools
        context.set("user_id", user_id)

        game_message = Message(
            from_agent="api_route",  # Identify the source
            to_agent="game_designer",  # Target agent
            tool="create_game",  # Tool to execute
            params={  # Parameters for the tool
                "user_id": user_id,
                "difficulty": difficulty,
                "game_type": game_type
                # Add other necessary params based on your tool definition
            }
        )

        print(f"Processing message via MCP server: {game_message.tool}")
        # Process the message through the MCP server
        game_data = await mcp_coordinator.server.process_message(game_message, context)

        # Check if the processing resulted in an error
        if isinstance(game_data, dict) and game_data.get("error"):
            raise Exception(f"MCP Error: {game_data['error']}")

        # Save the generated game to database
        print(f"Game data received from MCP: {type(game_data)}")
        game_id = db.store_game(user_id, game_data)  # Remove await here

        # Return the game data to the client
        return jsonify({
            "success": True,
            "game": {
                "game_id": str(game_id),
                "title": game_data.get("title", "Novo Jogo"),
                "difficulty": game_data.get("difficulty"),
                "game_type": game_data.get("game_type"),
                "content": game_data.get("exercises", [])
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
                "hint": exercise.get("hint", exercise.get("tip", "Fale devagar e claramente")),
                "visual_cue": exercise.get("visual_cue", exercise.get("word", "")),
                "type": exercise.get("type", "pronunciation"),
                "index": idx,
                "feedback": exercise.get("feedback", {})
            }
            exercises.append(transformed_exercise)

        # Adicionar os exercícios transformados ao objeto do jogo
        transformed_game["exercises"] = exercises
        # Adicionar content como alias de exercises
        transformed_game["content"] = exercises

        print(f"Retornando jogo transformado com {len(exercises)} exercícios")
        return jsonify({
            "success": True,
            "game": transformed_game
        })

    except Exception as e:
        print(f"❌ Erro ao buscar jogo: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Failed to fetch game: {str(e)}"
        }), 500


@app.route('/api/user/journey', methods=['GET'])
@token_required
def get_user_journey(user_id):
    """Endpoint para obter a jornada/progresso do usuário"""
    try:
        print(f"Buscando jogos completos para o usuário: {user_id}")
        completed_games = db.get_completed_games(user_id)

        # Contar jogos concluídos e calcular pontuação total
        total_games = len(completed_games)
        magic_points = total_games  # Cada jogo concluído vale 1 ponto de magia

        # Calcular há quantos dias o usuário está jogando
        first_game = None
        if completed_games:
            # Ordenar por data e pegar o primeiro jogo
            sorted_games = sorted(completed_games,
                                  key=lambda x: x.get('completed_at', x.get('created_at', '')))
            first_game = sorted_games[0]

        days_playing = 1  # Valor padrão
        if first_game and 'completed_at' in first_game:
            first_date = datetime.datetime.fromisoformat(
                first_game['completed_at'].replace('Z', '+00:00'))
            days_playing = (datetime.datetime.now() - first_date).days + 1

        print(
            f"Usuário {user_id}: {total_games} desafios, {magic_points} pontos de magia, {days_playing} dias de aventura")

        return jsonify({
            "success": True,
            "journey": {
                "completed_games": total_games,
                "magic_points": magic_points,
                "days_playing": days_playing,
                "games": completed_games  # Incluir detalhes dos jogos se necessário
            }
        })

    except Exception as e:
        print(f"Erro ao buscar jornada do usuário: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Failed to fetch user journey: {str(e)}"
        }), 500


@app.route('/api/game/finish', methods=['POST'])
@token_required
def finish_game(user_id):
    """
    Endpoint para finalizar uma sessão de jogo e salvar o progresso
    """
    try:
        data = request.json

        if not data or 'session_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing session_id parameter'
            }), 400

        session_id = data.get('session_id')
        completion_option = data.get('completion_option', 'complete')
        final_score = data.get('final_score', 0)
        completed_manually = data.get('completed_manually', True)

        print(
            f"Finalizando jogo: session_id={session_id}, option={completion_option}, score={final_score}")

        # Verificar se a sessão pertence ao usuário autenticado
        session = db.get_session(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        if session.get('user_id') != user_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to session'
            }), 403

        # Atualizar o status da sessão no banco de dados
        update_data = {
            'completed': True,
            'completion_status': completion_option,
            'final_score': final_score,
            'end_time': datetime.datetime.now().isoformat(),
            'completed_manually': completed_manually
        }

        db.update_session(session_id, update_data)

        # Atualizar o histórico do usuário
        user = db.get_user_by_id(user_id)
        if user:
            # Obter ou inicializar o histórico
            history = user.get('history', {})
            if 'completed_sessions' not in history:
                history['completed_sessions'] = []

            # Criar resumo da sessão
            session_summary = {
                'session_id': session_id,
                'game_id': session.get('game_id'),
                'title': session.get('title', 'Jogo sem título'),
                'completed_at': datetime.datetime.now().isoformat(),
                'score': final_score,
                'completion_type': completion_option,
                'difficulty': session.get('difficulty', 'iniciante')
            }

            # Adicionar ao histórico
            history['completed_sessions'].append(session_summary)

            # Atualizar usuário
            db.update_user(user_id, {'history': history})

        return jsonify({
            'success': True,
            'message': 'Game session completed successfully',
            'session_id': session_id
        })

    except Exception as e:
        print(f"❌ Erro ao finalizar jogo: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error finishing game: {str(e)}'
        }), 500


if __name__ == "__main__":
    import uvicorn
    import os
    from asgiref.wsgi import WsgiToAsgi  # Import the adapter

    # Get DEBUG setting from config or environment
    try:
        from config import DEBUG
    except ImportError:
        DEBUG = os.environ.get("FLASK_ENV") == "development" or os.environ.get(
            "FLASK_DEBUG") == "1"
        print(f"DEBUG setting fallback: {DEBUG}")

    port = int(os.environ.get('PORT', 5001))
    print(f"Starting server with Uvicorn (via app.py) on port {port}...")

    # Wrap the Flask WSGI app to make it ASGI compatible
    asgi_app = WsgiToAsgi(app)

    # Run the wrapped ASGI app with Uvicorn
    uvicorn.run(
        asgi_app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
