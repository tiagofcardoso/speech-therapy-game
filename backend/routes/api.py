from flask import Blueprint, jsonify, request
from auth.auth_middleware import token_required
from database.db_connector import get_user_history, get_user_statistics, get_user_achievements

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
