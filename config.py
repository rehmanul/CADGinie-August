import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Autodesk Forge
    FORGE_CLIENT_ID = os.getenv('FORGE_CLIENT_ID', 'bZCKOFynve2w4rpzNYmooBYAGuqxKWelBTiGcfdoSUpVlD0r')
    FORGE_CLIENT_SECRET = os.getenv('FORGE_CLIENT_SECRET')
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    
    # File Upload
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024  # 64MB
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'output_files'