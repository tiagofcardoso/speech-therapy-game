from functools import wraps
from flask import request, jsonify, g
import jwt
from config import JWT_SECRET_KEY

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Obter token do header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
                print(f"Token recebido: {token[:15]}...")
            except IndexError:
                print("Formato de Authorization header inválido")
                return jsonify({'message': 'Token is missing!'}), 401
        
        if not token:
            print("Token não encontrado no header")
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Decodificar token
            print(f"Decodificando token com chave: {JWT_SECRET_KEY[:10]}...")
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            print(f"Token decodificado: {data}")
            
            # Armazenar user_id no objeto g do Flask
            g.user_id = data['user_id']
            print(f"User ID extraído do token: {g.user_id}")
            
            # Passar para a função decorada
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            print("Token expirado")
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError as e:
            print(f"Token inválido: {str(e)}")
            return jsonify({'message': 'Invalid token!'}), 401
    
    return decorated