import os
from datetime import datetime

class Config:
    
    # Base directory of the application
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    
    # Create necessary directories
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Database configuration
    DATABASE = os.path.join(BASE_DIR, 'JapaneseDB.db')
    TESTING = False

    # Logging configuration
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(LOGS_DIR, f'app.log')
    LOG_LEVEL = 'INFO'

@staticmethod
def configure_logging(app):
    if not app.debug and not app.testing:
        # Only log once in production/development
        handler = logging.FileHandler('logs/app.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

class TestConfig(Config):
    TESTING = True
    
    @staticmethod
    def configure_logging(app):
        # Disable duplicate logging in tests
        if not hasattr(app, '_test_logging_configured'):
            handler = logging.FileHandler('logs/test.log')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            app.logger.addHandler(handler)
            app.logger.setLevel(logging.DEBUG)
            app._test_logging_configured = True

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'