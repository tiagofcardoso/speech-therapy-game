import os
from dotenv import load_dotenv
import urllib.parse
from flask import Flask
from flask_cors import CORS

# Carrega variáveis de ambiente
project_root = os.path.dirname(os.path.dirname(__file__))
dotenv_path = os.path.join(project_root, '.env')

if os.path.exists(dotenv_path):
    print(f"Carregando variáveis de ambiente de: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("AVISO: Arquivo .env não encontrado!")

# API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# MongoDB Configuration
MONGO_USERNAME = os.environ.get('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', '')

# Codifica as credenciais
MONGO_USERNAME_ENCODED = urllib.parse.quote_plus(MONGO_USERNAME)
MONGO_PASSWORD_ENCODED = urllib.parse.quote_plus(MONGO_PASSWORD)

# Constrói uma nova URI com credenciais escapadas
MONGODB_URI = f"mongodb://{MONGO_USERNAME_ENCODED}:{MONGO_PASSWORD_ENCODED}@{'mongodb' if os.environ.get('ENVIRONMENT') == 'development' else 'localhost'}:27017/speech_therapy_db?authSource=admin"

print(f"MongoDB URI (com credenciais escapadas): {MONGODB_URI}")

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', '9f42e347d8c1a650b5e8c2e2d950f41b3ec5e50511d3d76b9e086c96a20b1aa7')

# Debug mode
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Create the Flask app instance
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'seu_segredo_padrao_aqui')

# Configure CORS
CORS(app)
