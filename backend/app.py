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
import traceback
import time
import uuid
import base64
import tempfile
import subprocess
import asyncio
from asgiref.sync import async_to_sync
from functools import wraps
from functools import lru_cache
from ai.agents.speech_evaluator_agent import SpeechEvaluatorAgent
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

if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent
    sys.path.insert(0, str(project_root))


def async_route(f):
    """Wrapper for async route handlers"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return async_to_sync(f)(*args, **kwargs)
    return wrapper


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


load_dotenv()

if not OPENAI_API_KEY:
    print("\n⚠️  WARNING: OPENAI_API_KEY not set in environment!")
    print("   The application will fail when calling OpenAI services.")
    print("   Set this in your .env file.\n")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.register_blueprint(api_bp, url_prefix='/api')

CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

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


app.json_encoder = CustomJSONEncoder


@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})


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


auth_service = AuthService()
db = DatabaseConnector()

game_generator = None
mcp_coordinator = None

lipsync_generator = LipsyncGenerator()


@app.before_request
def initialize_services():
    global game_generator, mcp_coordinator, db

    if game_generator is None or mcp_coordinator is None:
        try:
            game_generator = GameGenerator()
            mcp_coordinator = MCPSystem(
                api_key=OPENAI_API_KEY, db_connector=db)
            print("MCP System initialized with database connection")
        except Exception as e:
            print(f"Error initializing services: {str(e)}")


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


def generate_token(user_id):
    print(f"JWT_SECRET_KEY utilizada: {JWT_SECRET_KEY}")
    try:
        payload = {
            'user_id': str(user_id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(
            payload,
            JWT_SECRET_KEY,
            algorithm='HS256'
        )

        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
    except Exception as e:
        print(f"Erro ao gerar token: {str(e)}")
        raise


def verify_token(token):
    try:
        # Handle case where token might be bytes
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return data
    except Exception as e:
        print(f"Erro ao decodificar token: {str(e)}")
        return None


@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    print("==== Recebida requisição de login ====")
    print(f"Método: {request.method}")

    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.get_json()
        print(f"Dados de login: {data}")

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username e senha são obrigatórios"
            }), 400

        user = db.authenticate_user(username, password)

        if not user:
            return jsonify({
                "success": False,
                "message": "Username ou senha inválidos"
            }), 401

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
    print("==== Recebida requisição de registro ====")
    print(f"Método: {request.method}")

    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.get_json()
        print(f"Dados de registro: {data}")

        if not data.get('username') or not data.get('password') or not data.get('name'):
            return jsonify({
                "success": False,
                "message": "Nome, username e senha são obrigatórios"
            }), 400

        if db.user_exists(data.get('username')):
            print(f"Usuário '{data.get('username')}' já existe")
            return jsonify({
                "success": False,
                "message": "Este nome de usuário já está em uso. Por favor, escolha outro."
            }), 409

        user_id = db.create_user(data)

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
    return jsonify({"success": True, "valid": True, "user_id": user_id}), 200


@app.route('/api/auth/test-token', methods=['GET'])
def test_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token não encontrado no header'}), 401

    try:
        token = auth_header.split(" ")[1]

        print(f"Testando token: {token[:10]}...")
        print(f"Chave JWT: {JWT_SECRET_KEY[:5]}...")

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


@app.route('/api/user/profile/<user_id>', methods=['GET'])
@token_required
def get_user_profile(user_id, requesting_user_id):
    try:
        print(f"Fetching profile for user_id: {user_id}")
        print(f"Requesting user_id: {requesting_user_id}")

        if user_id != requesting_user_id:
            print(
                f"Access denied: {requesting_user_id} trying to access {user_id}")
            return jsonify({"error": "Unauthorized access"}), 403

        user = db.get_user_by_id(user_id)

        if not user:
            print(f"User not found: {user_id}")
            return jsonify({"error": "User not found"}), 404

        if "password" in user:
            del user["password"]

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
    if user_id != requesting_user_id:
        return jsonify({"error": "Unauthorized access to update user profile"}), 403

    data = request.json

    allowed_fields = ["name", "age"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    success = db.update_user(user_id, update_data)

    if not success:
        return jsonify({"error": "Failed to update user profile"}), 500

    return jsonify({"success": True, "message": "Profile updated successfully"}), 200


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

    session_data = db.get_session(session_id)
    if not session_data:
        return jsonify({"error": "Session not found"}), 404

    if session_data.get("user_id") != user_id:
        return jsonify({"error": "Unauthorized access to session"}), 403

    evaluation_results = mcp_coordinator.process_response(
        session_data, recognized_text)

    if "session_complete" in evaluation_results and evaluation_results["session_complete"]:
        responses = session_data.get("responses", [])
        total_score = sum(r.get("score", 0) for r in responses)
        exercises_count = len(session_data.get("exercises", []))

        if exercises_count > 0:
            final_score_percentage = (
                total_score / (exercises_count * 10)) * 100
        else:
            final_score_percentage = 0

        difficulty = session_data.get("difficulty", "iniciante")
        completion_threshold = {
            "iniciante": 80,
            "médio": 90,
            "avançado": 100
        }.get(difficulty, 80)

        is_completed = final_score_percentage >= completion_threshold

        db.update_session(session_id, {
            "completed": is_completed,
            "final_score": final_score_percentage,
            "completion_status": "completed" if is_completed else "attempted",
            "end_time": datetime.datetime.now().isoformat()
        })

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

        return jsonify({
            "session_complete": True,
            "feedback": evaluation_results.get("feedback", {}),
            "final_score": final_score_percentage,
            "passed_threshold": is_completed,
            "completion_status": "completed" if is_completed else "need_improvement",
            "completion_threshold": completion_threshold
        }), 200


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
def synthesize_with_polly(user_id):
    """Endpoint para sintetizar fala usando AWS Polly"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400

        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': 'Empty text'}), 400

        print(f"📝 Texto para síntese com Polly: '{text}'")

        # Create voice settings using voice_id if provided
        voice_settings = {
            'voice_id': data.get('voice_id', 'Ines'),
            'engine': data.get('engine', 'standard'),
            'language_code': data.get('language_code', 'pt-PT'),
            'sample_rate': data.get('sample_rate', '22050')
        }

        # Use AWS Polly via the synthesis module
        audio_data = synthesize_speech(text, voice_settings)

        if not audio_data:
            return jsonify({'error': 'Failed to generate audio with AWS Polly'}), 500

        # Fix for bytes serialization issue - ensure we have string data
        if isinstance(audio_data, bytes):
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        else:
            # If it's already a string, use it directly
            audio_b64 = audio_data

        print(f"✅ Áudio Polly gerado: {len(audio_b64)} caracteres")

        return jsonify({'success': True, 'audio': audio_b64})
    except Exception as e:
        print(f"❌ Erro na síntese com Polly: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Synthesis error: {str(e)}'}), 500


@app.route('/api/synthesize-speech', methods=['POST'])
def synthesize_speech_endpoint():
    """Endpoint para sintetizar fala a partir de texto"""
    try:
        print("Processando solicitação de síntese de fala")
        data = request.json

        if not data or 'text' not in data:
            print("❌ Dados de entrada inválidos")
            return Response(
                json.dumps(
                    {'success': False, 'error': 'Missing text parameter'}),
                mimetype='application/json',
                status=400
            )

        text = data.get('text', '').strip()
        if not text:
            print("❌ Texto vazio")
            return Response(
                json.dumps({'success': False, 'error': 'Empty text'}),
                mimetype='application/json',
                status=400
            )

        print(f"📝 Texto para síntese: '{text}'")

        try:
            from gtts import gTTS
            import io

            mp3_fp = io.BytesIO()
            tts = gTTS(text=text, lang='pt', slow=False)
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            audio_bytes = mp3_fp.read()

            if not audio_bytes:
                print("❌ Falha ao gerar áudio - nenhum dado retornado")
                return Response(
                    json.dumps(
                        {'success': False, 'error': 'Failed to generate audio'}),
                    mimetype='application/json',
                    status=500
                )

            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            print(
                f"✅ Áudio gerado com sucesso: {len(audio_bytes)} bytes ({len(audio_b64)} caracteres em base64)")

            result = {'success': True, 'audio_data': audio_b64}
            json_str = json.dumps(result)

            return Response(
                json_str,
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

        from gtts import gTTS
        import io

        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang='pt')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        audio_b64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
        print(f"TTS simples: Áudio gerado com {len(audio_b64)} caracteres")

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
    """Endpoint para avaliar a pronúncia do usuário"""
    try:
        if 'audio' not in request.files:
            print("❌ Nenhum arquivo de áudio na requisição")
            return jsonify({
                "success": False,
                "message": "No audio file provided",
                "error_code": "NO_AUDIO"
            }), 400

        audio_file = request.files['audio']
        expected_word = request.form.get('expected_word', '').strip()
        session_id = request.form.get('session_id')

        if not expected_word:
            print("❌ Palavra esperada não fornecida")
            return jsonify({
                "success": False,
                "message": "Expected word not provided",
                "error_code": "NO_EXPECTED_WORD"
            }), 400

        print(f"📊 Avaliando pronúncia:")
        print(
            f"- Arquivo de áudio: {audio_file.filename} ({audio_file.content_type})")
        print(f"- Palavra esperada: '{expected_word}'")
        print(f"- ID do usuário: {user_id}")
        if session_id:
            print(f"- ID da sessão: {session_id}")

        audio_file.seek(0, os.SEEK_END)
        file_size = audio_file.tell()
        audio_file.seek(0)

        print(f"- Tamanho do arquivo: {file_size} bytes")
        if file_size < 100:
            print("❌ Arquivo de áudio muito pequeno")
            return jsonify({
                "success": False,
                "message": "Audio file is too small",
                "error_code": "SMALL_AUDIO"
            }), 400

        try:
            evaluation_result = await mcp_coordinator.evaluate_pronunciation(
                audio_file=audio_file,
                expected_word=expected_word,
                user_id=user_id,
                session_id=session_id
            )

            if not evaluation_result:
                print("❌ Resultado da avaliação vazio")
                return jsonify({
                    "success": False,
                    "message": "Empty evaluation result from coordinator",
                    "error_code": "EMPTY_RESULT"
                }), 500

            log_result = evaluation_result.copy() if isinstance(
                evaluation_result, dict) else {"error": "Non-dict result"}

            if "audio_feedback" in log_result and isinstance(log_result["audio_feedback"], str):
                audio_len = len(log_result["audio_feedback"])
                log_result["audio_feedback"] = f"<audio_data: {audio_len} chars>"

            print(
                f"✅ Resultado da avaliação: {json.dumps(log_result, indent=2)}")

            if not evaluation_result.get("audio_feedback") and evaluation_result.get("feedback"):
                feedback_text = evaluation_result.get("feedback")
                print(f"🔊 Gerando áudio de feedback para: '{feedback_text}'")
                try:
                    from gtts import gTTS
                    import io

                    audio_io = io.BytesIO()
                    tts = gTTS(text=feedback_text, lang='pt', slow=False)
                    tts.write_to_fp(audio_io)
                    audio_io.seek(0)

                    audio_bytes = audio_io.read()
                    evaluation_result["audio_feedback"] = base64.b64encode(
                        audio_bytes).decode('utf-8')
                    print(
                        f"✅ Áudio de feedback gerado: {len(evaluation_result['audio_feedback'])} caracteres")
                except Exception as tts_error:
                    print(
                        f"⚠️ Erro ao gerar áudio de feedback: {str(tts_error)}")

            status_code = 200 if evaluation_result.get("success") else 500
            return jsonify(evaluation_result), status_code

        except Exception as coord_error:
            print(f"❌ Erro ao chamar o coordenador: {str(coord_error)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "message": f"Coordinator error: {str(coord_error)}",
                "error_code": "COORDINATOR_ERROR"
            }), 500

    except Exception as e:
        print(f"❌ Erro geral na avaliação de pronúncia: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "error_code": "ENDPOINT_ERROR"
        }), 500


@app.route('/api/gigi/generate-game', methods=['POST'])
@token_required
def gigi_game_post(user_id):
    """Handler para requisições POST no endpoint de geração de jogos Gigi"""
    try:
        print(f"✅ Iniciando geração de jogo via Gigi para usuário: {user_id}")

        # Obter parâmetros da requisição
        data = request.get_json() or {}
        print(f"📝 Dados da requisição: {data}")

        # Mapear dificuldade
        game_type = data.get('game_type', "exercícios de pronúncia")

        difficulty_map = {
            'advanced': 'avançado',
            'medium': 'médio',
            'beginner': 'iniciante'
        }
        requested_difficulty = data.get('difficulty', 'beginner')
        difficulty = difficulty_map.get(
            requested_difficulty.lower(), 'iniciante')

        print(
            f"🔄 Mapeando dificuldade: '{requested_difficulty}' → '{difficulty}'")

        # Verificar inicialização do MCP
        global mcp_coordinator
        if not mcp_coordinator:
            print("❌ MCP Coordinator não inicializado!")
            return jsonify({
                "success": False,
                "message": "Sistema de geração de jogos não disponível no momento."
            }), 500

        # Criar uma função aninhada para processar a requisição de forma assíncrona
        @async_to_sync
        async def process_game_request():
            try:
                # Set a shorter timeout for OpenAI request to ensure request doesn't hang too long
                import asyncio
                print("⏱️ Configurando timeout para criação de jogo: 40 segundos")

                # Process request with timeout
                try:
                    # Create a task with timeout
                    game_task = asyncio.create_task(generate_game_with_mcp())
                    game_data = await asyncio.wait_for(game_task, timeout=40.0)
                except asyncio.TimeoutError:
                    print("⏰ Timeout na geração do jogo após 40 segundos")
                    return {
                        "success": False,
                        "message": "A geração do jogo excedeu o tempo limite. Por favor, tente novamente."
                    }

                # Verificar se há erros
                if isinstance(game_data, dict) and "error" in game_data:
                    raise Exception(f"Erro do MCP: {game_data['error']}")

                # Salvar jogo no banco de dados
                print(f"💾 Salvando jogo gerado no banco de dados")
                game_id = db.store_game(user_id, game_data)

                # Retornar dados do jogo
                return {
                    "success": True,
                    "game": {
                        "game_id": str(game_id),
                        "title": game_data.get("title", "Novo Jogo"),
                        "difficulty": game_data.get("difficulty", difficulty),
                        "game_type": game_data.get("game_type", game_type),
                        "content": game_data.get("exercises", [])
                    }
                }
            except Exception as inner_error:
                print(
                    f"❌ Erro ao processar solicitação de jogo: {str(inner_error)}")
                traceback.print_exc()
                return {
                    "success": False,
                    "message": f"Falha na geração do jogo: {str(inner_error)}"
                }

        async def generate_game_with_mcp():
            # Preparar contexto e mensagem para o agente de design de jogos
            context = ModelContext()
            context.set("user_id", user_id)

            # Criar mensagem para o MCP
            game_message = Message(
                from_agent="api",
                to_agent="game_designer",
                tool="create_game",
                params={
                    "user_id": user_id,
                    "difficulty": difficulty,
                    "game_type": game_type
                }
            )

            # Enviar solicitação para o MCP e aguardar resposta
            print(f"🔄 Processando mensagem: {game_message.tool}")
            return await mcp_coordinator.server.process_message(game_message, context)

        # Executar a função aninhada
        result = process_game_request()

        # Verificar sucesso da operação
        if result.get("success"):
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        print(f"❌ Erro global na rota /api/gigi/generate-game: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Erro no servidor: {str(e)}"
        }), 500


@app.route('/api/games/<game_id>', methods=['GET', 'OPTIONS'])
def get_game_endpoint(game_id):
    """Endpoint para obter os detalhes de um jogo específico"""
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

        # Verificar o formato do ID do jogo (pode ser string ou ObjectId)
        try:
            # Tentar converter para ObjectId (formato MongoDB)
            from bson.objectid import ObjectId
            if not ObjectId.is_valid(game_id):
                print(f"❌ ID de jogo inválido: {game_id}")
                return jsonify({
                    "success": False,
                    "message": "Invalid game ID format"
                }), 400
        except Exception as id_error:
            print(f"Erro na validação do ID: {str(id_error)}")
            # Continuar mesmo com erro, pode ser um formato válido diferente

        # Adicionar logs detalhados para depuração
        print(f"🔍 Buscando jogo no banco de dados com ID: {game_id}")

        # Buscar o jogo no banco de dados - corrigir aqui se o método db.get_game não estiver funcionando
        game = db.get_game(game_id)

        # Se o jogo não for encontrado, tentar uma busca alternativa (se existir um método diferente)
        if not game:
            print(
                f"⚠️ Jogo não encontrado usando db.get_game(). Tentando métodos alternativos...")
            # Exemplo: tentar buscar usando o método find_one diretamente
            try:
                from bson.objectid import ObjectId
                game = db.games_collection.find_one({"_id": ObjectId(game_id)})
                if game:
                    print(f"✅ Jogo encontrado usando consulta direta ao MongoDB")
            except Exception as alt_error:
                print(f"❌ Erro na busca alternativa: {str(alt_error)}")

        # Se ainda não encontrou o jogo, retornar erro
        if not game:
            print(f"❌ Jogo não encontrado: {game_id}")
            return jsonify({
                "success": False,
                "message": "Game not found"
            }), 404

        print(f"✅ Jogo encontrado: {game.get('title', 'Sem título')}")
        print(f"🔍 Estrutura do jogo: {type(game)}")

        # Dump the game structure for debugging
        import json
        try:
            # Convert ObjectId to string for JSON serialization
            game_dump = {k: str(v) if isinstance(v, ObjectId)
                         else v for k, v in game.items()}
            print(
                f"Estrutura completa do jogo: {json.dumps(game_dump, indent=2)}")
        except Exception as dump_error:
            print(f"Erro ao fazer dump do jogo: {str(dump_error)}")

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

        print(f"🔍 Encontrados {len(raw_exercises)} exercícios")

        # Log primeiro exercício para debug
        if raw_exercises and len(raw_exercises) > 0:
            print(f"Primeiro exercício: {raw_exercises[0]}")

        # Transformar os exercícios em um formato consistente
        for idx, exercise in enumerate(raw_exercises):
            if not isinstance(exercise, dict):
                print(f"⚠️ Pulando exercício não-dict: {exercise}")
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

        print(
            f"✅ Retornando jogo transformado com {len(exercises)} exercícios")
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


@app.route('/api/game/finish', methods=['POST', 'OPTIONS'])
def finish_game_handler():
    """Endpoint for finishing a game and recording its completion"""
    # Handle OPTIONS requests for CORS without authentication
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    # For POST requests, extract token and authenticate
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"success": False, "message": "No authorization header provided"}), 401

    try:
        # Extract and validate token
        token = auth_header.split(" ")[1] if len(
            auth_header.split(" ")) > 1 else auth_header
        token_data = verify_token(token)

        if not token_data or 'user_id' not in token_data:
            return jsonify({"success": False, "message": "Invalid token"}), 401

        user_id = token_data['user_id']

        # Now process the game completion
        try:
            print("🎮 Processing game completion")

            # Get request data
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "No data provided"}), 400

            # Extract necessary data
            session_id = data.get('session_id')
            if not session_id:
                return jsonify({"success": False, "message": "No session_id provided"}), 400

            # Get session data
            session_data = db.get_session(session_id)
            if not session_data:
                print(f"❌ Session not found: {session_id}")
                return jsonify({"success": False, "message": "Session not found"}), 404

            # Verify the user is authorized for this session
            session_user_id = session_data.get('user_id')
            if session_user_id and str(session_user_id) != str(user_id):
                print(
                    f"❌ Unauthorized user: {user_id} trying to complete session for {session_user_id}")
                return jsonify({"success": False, "message": "Unauthorized access to session"}), 403

            print(f"✅ Session data validated: {session_id} for user {user_id}")

            # Get game data
            game_id = session_data.get('game_id')
            if not game_id:
                print(f"❌ Game ID not found in session: {session_id}")
                return jsonify({"success": False, "message": "Game ID not found in session"}), 400

            # Extract additional parameters
            final_score = data.get('final_score', 0)
            completion_option = data.get('completion_option', 'complete')

            print(
                f"📊 Finishing game: game_id={game_id}, score={final_score}, option={completion_option}")

            # Update session
            session_update = {
                "completed": True,
                "end_time": datetime.datetime.now().isoformat(),
                "final_score": final_score,
                "completion_option": completion_option
            }

            session_success = db.update_session(session_id, session_update)
            if not session_success:
                print(f"⚠️ Warning: Failed to update session {session_id}")

            # Update game
            game_update = {
                "completed": True,
                "completed_at": datetime.datetime.now().isoformat(),
                "final_score": final_score
            }

            game_success = db.update_game(game_id, game_update)
            if not game_success:
                print(f"⚠️ Warning: Failed to update game {game_id}")

            # Add to user history
            history_entry = {
                "session_id": session_id,
                "game_id": str(game_id),
                "completed_at": datetime.datetime.now().isoformat(),
                "score": final_score,
                "difficulty": session_data.get("difficulty", "iniciante"),
                "game_type": session_data.get("game_type", "exercícios de pronúncia"),
                "completion_option": completion_option
            }

            history_success = db.add_to_user_history(user_id, history_entry)
            if not history_success:
                print(
                    f"⚠️ Warning: Failed to update user history for {user_id}")

            print(f"✅ Game successfully completed: {game_id}")

            # Return success response
            return jsonify({
                "success": True,
                "message": "Game completed successfully",
                "game_id": str(game_id),
                "session_id": session_id,
                "final_score": final_score
            })

        except Exception as e:
            print(f"❌ Error completing game: {str(e)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "message": f"Error completing game: {str(e)}"
            }), 500

    except Exception as auth_error:
        print(f"❌ Authentication error: {str(auth_error)}")
        return jsonify({"success": False, "message": f"Authentication failed: {str(auth_error)}"}), 401


if __name__ == "__main__":
    import os
    import uvicorn
    from asgiref.wsgi import WsgiToAsgi

    try:
        from config import DEBUG
        DEBUG = os.environ.get("FLASK_ENV") == "development" or os.environ.get(
            "FLASK_DEBUG") == "1"
    except ImportError:
        DEBUG = False

    port = int(os.environ.get('PORT', 5001))
    print(f"Starting server with Uvicorn (via app.py) on port {port}...")

    asgi_app = WsgiToAsgi(app)

    uvicorn.run(
        asgi_app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
