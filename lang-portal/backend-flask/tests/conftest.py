import pytest
from app import create_app
from flask import g

@pytest.fixture
def app():
    """Create and configure a test Flask app instance"""
    app = create_app({
        'TESTING': True,
        'DATABASE': ':memory:'  # Use in-memory SQLite for testing
    })
    
    return app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def app_context(app):
    """Create an application context"""
    with app.app_context() as ctx:
        # Initialize test database
        cursor = app.db.get().cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                words_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kanji TEXT NOT NULL,
                english TEXT NOT NULL,
                romaji TEXT NOT NULL,
                parts TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS word_groups (
                word_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                FOREIGN KEY (word_id) REFERENCES words(id),
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        ''')
        
        app.db.get().commit()
        
        yield ctx
        
        # Clean up after test
        cursor.execute('DROP TABLE IF EXISTS word_groups')
        cursor.execute('DROP TABLE IF EXISTS words')
        cursor.execute('DROP TABLE IF EXISTS groups')
        app.db.get().commit()
        app.db.close() 