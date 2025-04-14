from flask import Blueprint, jsonify, request
from auth.auth_middleware import token_required
from database.db_connector import get_user_history, get_user_statistics, get_user_achievements
# Importando a função de síntese do módulo speech
from speech.synthesis import synthesize_speech

api_bp = Blueprint('api', __name__)


@api_bp.route('/user/history', methods=['GET'])
@token_required
def user_history(current_user):
    """
    Endpoint para obter o histórico de jogos do usuário.
    """
    try:
        user_id = current_user['user_id']
        history = get_user_history(user_id)

        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar histórico: {str(e)}'
        }), 500


@api_bp.route('/user/statistics', methods=['GET'])
@token_required
def user_statistics(current_user):
    """
    Endpoint para obter estatísticas de progresso do usuário.
    """
    try:
        user_id = current_user['user_id']
        statistics = get_user_statistics(user_id)

        return jsonify({
            'success': True,
            'statistics': statistics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar estatísticas: {str(e)}'
        }), 500


@api_bp.route('/user/achievements', methods=['GET'])
@token_required
def user_achievements(current_user):
    """
    Endpoint para obter as conquistas do usuário.
    """
    try:
        user_id = current_user['user_id']
        achievements = get_user_achievements(user_id)

        return jsonify({
            'success': True,
            'achievements': achievements
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar conquistas: {str(e)}'
        }), 500


@api_bp.route('/synthesize-speech', methods=['POST'])
def synthesize_speech_endpoint():
    """
    Endpoint para sintetizar fala usando AWS Polly.
    Recebe um texto e retorna o áudio em formato base64.
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'message': 'O texto para sintetizar é obrigatório'
            }), 400

        text = data['text']
        voice_settings = data.get('voice_settings')

        print(f"Processando solicitação de síntese de fala")
        print(f"📝 Texto para síntese: '{text}'")
        print(f"🔊 Configurações de voz: {voice_settings}")

        # Usar o serviço de síntese para gerar o áudio
        audio_data = synthesize_speech(text, voice_settings)

        if not audio_data:
            return jsonify({
                'success': False,
                'message': 'Falha ao sintetizar o texto'
            }), 500

        print(f"✅ Áudio sintetizado com sucesso.")
        return jsonify({
            'success': True,
            'audio_data': audio_data,
            'text': text,
            'timestamp': int(time.time())
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao sintetizar fala: {str(e)}'
        }), 500
