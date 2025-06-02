import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
    S3_BUCKET = os.getenv('S3_BUCKET')
    
    # MySQL Database Configuration
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'kokorito_default_secret')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Image Configuration
    MAX_IMAGE_WIDTH = 1200
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'} 