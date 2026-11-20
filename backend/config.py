import os
from datetime import timedelta
import pytz
from dotenv import load_dotenv

# Load .env from backend or root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def resolve_database_uri():
    custom_url = os.getenv('DATABASE_URL')
    if custom_url:
        return custom_url

    db_type = os.getenv('DB_TYPE', 'auto').lower()
    sqlite_url = f"sqlite:///{os.path.join(BASE_DIR, 'academic_assistant.db')}"

    if db_type == 'sqlite' or os.getenv('TESTING') == 'True':
        return sqlite_url

    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_db = os.getenv('MYSQL_DB', 'academic_assistant')
    mysql_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}?charset=utf8mb4"

    # Test if MySQL server is reachable with configured credentials
    try:
        import pymysql
        conn = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            connect_timeout=1
        )
        conn.close()
        return mysql_url
    except Exception:
        return sqlite_url

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'college-academic-secret-key-super-secure-2026')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-academic-secret-token-key-2026')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 24)))
    
    # System Timezone (Default: Asia/Kolkata)
    TIMEZONE_STR = os.getenv('TIMEZONE', 'Asia/Kolkata')
    TIMEZONE = pytz.timezone(TIMEZONE_STR)

    # Database Configuration
    DB_TYPE = os.getenv('DB_TYPE', 'auto').lower()
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_DB = os.getenv('MYSQL_DB', 'academic_assistant')
    
    SQLALCHEMY_DATABASE_URI = resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # 16 MB
    ALLOWED_EXTENSIONS = {'pdf'}

    # AI Chatbot & RAG configuration
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'none').lower() # 'gemini', 'openai', or 'none'
    AI_API_KEY = os.getenv('AI_API_KEY', '').strip()
    
    # Department Contacts for fallback queries
    OFFICIAL_DEPT_CONTACT = os.getenv(
        'OFFICIAL_DEPT_CONTACT',
        'Dean of Academic Affairs (academics@college.edu | 044-2251-8000)'
    )
    COE_CONTACT = os.getenv(
        'COE_CONTACT',
        'Controller of Examinations (coe@college.edu | 044-2251-8001)'
    )
    
    # Scheduler
    SCHEDULER_API_ENABLED = False
