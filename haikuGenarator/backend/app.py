from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to the database file in the parent directory
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'haiku_generator.db')

def get_db_connection():
    """Create a database connection and set row_factory to sqlite3.Row"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the haikus table if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the haikus table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS haikus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_word TEXT NOT NULL,
        language TEXT NOT NULL,
        haiku_text TEXT NOT NULL,
        image_data BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized with haikus table")

@app.route('/')
def index():
    """Root URL providing basic information about the API"""
    return jsonify({
        'message': 'Welcome to the Haiku Generator API',
        'endpoints': {
            'GET /api/haikus': 'Retrieve all haikus',
            'POST /api/haikus': 'Create a new haiku',
            'GET /api/health': 'Health check endpoint'
        }
    })

@app.route('/api/haikus', methods=['GET'])
def get_haikus():
    """Get all haikus from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM haikus ORDER BY created_at DESC')
        haikus = cursor.fetchall()
        
        # Convert rows to dictionaries
        result = []
        for haiku in haikus:
            result.append({
                'id': haiku['id'],
                'input_word': haiku['input_word'],
                'language': haiku['language'],
                'haiku_text': haiku['haiku_text'],
                'image_data': haiku['image_data'],
                'created_at': haiku['created_at']
            })
        
        conn.close()
        logger.info("Fetched haikus from database")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting haikus: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/haikus', methods=['POST'])
def create_haiku():
    """Create a new haiku in the database"""
    try:
        data = request.json
        # logger.info(f"Incoming data: {data}")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO haikus (input_word, language, haiku_text, image_data, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            data['input_word'],
            data['language'],
            data['haiku_text'],
            data['image_data'],
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        logger.info("Haiku created successfully")
        
        return jsonify({'success': True}), 201
    except Exception as e:
        logger.error(f"Error creating haiku: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_exists = os.path.exists(db_path)
    logger.info(f"Health check: database exists: {db_exists}")
    return jsonify({'status': 'healthy', 'database': db_exists}), 200

if __name__ == '__main__':
    # Initialize the database before starting the server
    init_db()
    # Run the Flask application
    app.run(port=5001, debug=True)