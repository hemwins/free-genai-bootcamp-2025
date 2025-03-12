from flask import Flask, g
from flask_cors import CORS
from config import Config, TestConfig, DevelopmentConfig
from lib.db import Db
import logging
from logging.handlers import RotatingFileHandler
import os

import routes.vocabulary
import routes.words
import routes.groups
import routes.study_sessions
import routes.dashboard
import routes.study_activities

def get_allowed_origins(app):
    try:
        cursor = app.db.cursor()
        cursor.execute('SELECT url FROM study_activities')
        urls = cursor.fetchall()
        # Convert URLs to origins (e.g., https://example.com/app -> https://example.com)
        origins = set()
        for url in urls:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url['url'])
                origin = f"{parsed.scheme}://{parsed.netloc}"
                origins.add(origin)
            except:
                continue
        return list(origins) if origins else ["*"]
    except:
        return ["*"]  # Fallback to allow all origins if there's an error

def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        # Use development config by default
        app.config.from_object(DevelopmentConfig)
    else:
        # Use test config for testing
        app.config.from_object(TestConfig)
    
    # Setup logging
    setup_logging(app)
    
    # Initialize database using config
    app.db = Db(database=app.config['DATABASE'])
    
    # Log database initialization
    app.logger.info(f"Database initialized: {app.config['DATABASE']}")
      
    # Single CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Register database connection management
    app.teardown_appcontext(app.db.close)

    # load routes
    routes.words.load(app)
    routes.groups.load(app)
    routes.study_sessions.load(app)
    routes.dashboard.load(app)
    routes.study_activities.load(app)
    routes.vocabulary.load(app)
    return app

def setup_logging(app):
    # Create formatter
    formatter = logging.Formatter(app.config['LOG_FORMAT'])
    
    # Create file handler
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(app.config['LOG_LEVEL'])
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(app.config['LOG_LEVEL'])
    
    # First log message
    app.logger.info('Logger initialized')

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=4999)