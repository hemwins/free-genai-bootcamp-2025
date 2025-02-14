import pytest
from flask import json
from datetime import datetime, timedelta

def test_get_recent_session(client, setup_test_db):
    """Test getting the most recent study session"""
    # First create a test session with reviews
    with client.application.app_context():
        cursor = setup_test_db.cursor()
        
        # Insert test session
        cursor.execute('''
            INSERT INTO study_sessions (id, group_id, study_activity_id, created_at)
            VALUES (1, 1, 1, datetime('now'))
        ''')
        
        # Insert some word review items
        cursor.execute('''
            INSERT INTO word_review_items (study_session_id, correct)
            VALUES 
                (1, 1),  -- correct answer
                (1, 1),  -- correct answer
                (1, 0)   -- wrong answer
        ''')
        setup_test_db.commit()
    
    # Test the endpoint
    response = client.get('/api/dashboard/recent-session')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'session' in data
    assert data['session']['correct_count'] == 2
    assert data['session']['wrong_count'] == 1

def test_get_recent_session_no_data(client):
    """Test getting recent session when no sessions exist"""
    response = client.get('/api/dashboard/recent-session')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'No recent sessions found'

def test_get_dashboard_stats(client, setup_test_db):
    """Test getting dashboard statistics"""
    # Setup test data
    with client.application.app_context():
        cursor = setup_test_db.cursor()
        
        # Create sessions across different dates
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute('''
            INSERT INTO study_sessions (group_id, study_activity_id, created_at)
            VALUES 
                (1, 1, ?),  -- today
                (1, 1, ?),  -- yesterday
                (1, 1, ?)   -- yesterday
        ''', (datetime.now(), yesterday, yesterday))
        
        # Add review items
        cursor.execute('''
            INSERT INTO word_review_items (study_session_id, correct)
            VALUES 
                (1, 1), (1, 0),  -- 50% accuracy
                (2, 1), (2, 1),  -- 100% accuracy
                (3, 0), (3, 0)   -- 0% accuracy
        ''')
        setup_test_db.commit()
    
    response = client.get('/api/dashboard/stats')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'total_sessions' in data
    assert data['total_sessions'] == 3
    assert 'sessions_today' in data
    assert data['sessions_today'] == 1
    assert 'average_accuracy' in data
    assert isinstance(data['average_accuracy'], float)

def test_get_dashboard_stats_no_data(client):
    """Test getting dashboard stats when no data exists"""
    response = client.get('/api/dashboard/stats')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['total_sessions'] == 0
    assert data['sessions_today'] == 0
    assert data['average_accuracy'] == 0

@pytest.fixture(autouse=True)
def setup_test_data(app, setup_test_db):
    """Setup required test data"""
    with app.app_context():
        cursor = setup_test_db.cursor()
        
        # Insert test groups and activities
        cursor.execute('INSERT INTO groups (id, name) VALUES (1, "Test Group")')
        cursor.execute('INSERT INTO study_activities (id, name) VALUES (1, "Test Activity")')
        
        setup_test_db.commit()