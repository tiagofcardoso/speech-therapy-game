from functools import wraps
from flask import request, jsonify, g
from auth.auth_service import AuthService

auth_service = AuthService()

def token_required(f):
    """
    Decorator for routes that require authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"message": "Authentication token is missing", "authenticated": False}), 401
        
        # Verify token
        result = auth_service.verify_token(token)
        if not result.get("valid"):
            return jsonify({"message": "Invalid or expired token", "authenticated": False}), 401
        
        # Set user_id for the route
        user_id = result.get("user_id")
        kwargs['user_id'] = user_id
        g.user_id = user_id
        
        return f(*args, **kwargs)
    
    return decorated