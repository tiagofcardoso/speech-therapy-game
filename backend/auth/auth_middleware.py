from functools import wraps
from flask import request, jsonify, g
import jwt
from config import app  # Import from config instead of app

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token is missing!'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data['user_id']  # Store user_id in Flask's g object
            
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
    
    return decorated