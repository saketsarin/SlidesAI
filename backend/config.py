import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    CLIENT_SECRETS_FILE = "client_secrets.json"
    GOOGLE_SCOPES = [
        'https://www.googleapis.com/auth/presentations',
        'https://www.googleapis.com/auth/drive.file'
    ]
    MAX_POINTS_PER_SLIDE = 10
    MAX_POINT_LENGTH = 200
    FLASK_HOST = '127.0.0.1'
    FLASK_PORT = 5000
    DEBUG = False