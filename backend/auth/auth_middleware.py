from functools import wraps
from flask import request, jsonify, g
import jwt
from config import JWT_SECRET_KEY


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"message": "Bearer token malformed"}), 401

        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            print(f"Token recebido: {token[:15]}...")
            print(f"Decodificando token com chave: {JWT_SECRET_KEY[:10]}...")

            # Decodificar o token
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            user_id = data['user_id']
            print(f"Token decodificado: {data}")
            print(f"User ID extraído do token: {user_id}")

            # Passar o user_id para a função decorada
            kwargs['user_id'] = user_id
            return f(*args, **kwargs)

        except Exception as e:
            print(f"Erro ao decodificar token: {str(e)}")
            return jsonify({"message": f"Token inválido: {str(e)}"}), 401

    return decorated
