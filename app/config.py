"""Application configuration."""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, '..', 'instance', 'evaluator.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Code execution limits
    CODE_EXECUTION_TIMEOUT = 10  # seconds
    CODE_MAX_OUTPUT_LENGTH = 10000    # Upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
    ALLOWED_EXTENSIONS = {
        'documents': {'pdf', 'docx', 'doc', 'txt'},
        'code': {'py', 'java', 'cpp', 'c', 'h', 'hpp'}
    }
