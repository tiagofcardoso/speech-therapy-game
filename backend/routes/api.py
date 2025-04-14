from flask import Blueprint, jsonify, request
from auth.auth_middleware import token_required
from database.db_connector import get_user_history, get_user_statistics, get_user_achievements
# Importando a função de síntese do módulo speech
from speech.synthesis import synthesize_speech
import time

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


@api_bp.route('/user/journey', methods=['GET'])
@token_required
def user_journey(user_id):
    """
    Endpoint para obter os dados da jornada do usuário para o dashboard.
    - Total de desafios: número de jogos completados
    - Pontos de magia: média de pontuação de todos os jogos
    - Dias de aventura: número de dias de login consecutivos
    """
    try:
        from database.db_connector import DatabaseConnector
        from datetime import datetime, timedelta

        db = DatabaseConnector()

        # Obter usuário do banco de dados
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado'
            }), 404

        # 1. Desafios vencidos: considerar tanto as sessões no histórico quanto os jogos marcados como completos
        # 1.1 Buscar jogos marcados como completos diretamente da coleção de jogos (principal fonte de verdade)
        completed_games = db.get_completed_games(user_id)

        # Verificar se há jogos completos
        challenges_completed = len(completed_games)

        # 2. Pontos de magia: média de pontuação
        # Calcular pontuação apenas a partir dos jogos completos
        if challenges_completed > 0:
            total_games_score = sum(game.get('final_score', 0)
                                    for game in completed_games)
            magic_points = round(total_games_score / challenges_completed)
        else:
            magic_points = 0

        # 3. Dias de aventura: obtido do campo estatísticas ou valor padrão
        adventure_days = user.get('statistics', {}).get('consecutive_days', 1)

        # Log para debug (incluindo análise de dados)
        print(
            f"Usuário {user_id}: {challenges_completed} desafios, {magic_points} pontos de magia, {adventure_days} dias de aventura")

        return jsonify({
            'success': True,
            'journey': {
                'challenges_completed': challenges_completed,
                'magic_points': magic_points,
                'adventure_days': adventure_days
            }
        })

    except Exception as e:
        import traceback
        print(f"Erro ao buscar dados da jornada: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar dados da jornada: {str(e)}'
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
