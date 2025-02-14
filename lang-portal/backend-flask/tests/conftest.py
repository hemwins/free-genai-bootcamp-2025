import pytest
from app import create_app
from config import TestConfig
from lib.db import Db
from tests.test_helpers import print_table_contents
import logging
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config.from_object(TestConfig)
    
    # Ensure test logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    
    # Configure logging once for test session
    if not hasattr(app, '_test_logging_configured'):
        handler = logging.FileHandler('logs/test.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.DEBUG)
        app._test_logging_configured = True
    
    return app

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def setup_test_db(app):
    """Initialize test database before each test"""
    with app.app_context():
        db = app.db
        cursor = db.cursor()
        
         # Log database operations
        app.logger.info("Setting up test database")
        
        try:
            # Insert test data if not exists
            cursor.execute('INSERT OR IGNORE INTO groups (id, name) VALUES (1, "Test Group")')
            cursor.execute('INSERT OR IGNORE INTO study_activities (id, name) VALUES (1, "Test Activity")')
            db.commit()
            app.logger.info("Test data inserted successfully")
            
            print("\n=== Database State Before Test ===")
            print_table_contents(db, 'groups')
            print_table_contents(db, 'study_activities')
            
            yield db
            
            print("\n=== Database State After Test ===")
            print_table_contents(db, 'study_sessions')
            
            # Clean up test data after each test
            cursor.execute('DELETE FROM study_sessions WHERE created_at < datetime("now", "-1 hour")')
            db.commit()
            app.logger.info("Old test sessions cleaned up")
            
        except Exception as e:
            app.logger.error(f"Database setup error: {str(e)}")
            raise e

@pytest.fixture(scope='function')
def app_context(app):
    with app.app_context():
        yield
