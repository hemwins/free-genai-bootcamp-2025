import pytest
from flask import json
from tests.test_helpers import print_table_contents

def test_database_setup(app, setup_test_db):
    """Verify database content before tests"""
    with app.app_context():
        # Print contents of relevant tables
        print_table_contents(setup_test_db, 'groups')
        print_table_contents(setup_test_db, 'study_activities')
        print_table_contents(setup_test_db, 'study_sessions')

def setup_test_data(app, setup_test_db):
    """Setup test data before each test"""
    with app.app_context():
        cursor = setup_test_db.cursor() 
        # Insert test groups
        cursor.execute('''
            INSERT INTO groups (id, name) 
            VALUES (1, "Test Group 1"), (2, "Test Group 2")
        ''')    
        # Insert test activities
        cursor.execute('''
            INSERT INTO study_activities (id, name) 
            VALUES (1, "Test Activity 1"), (2, "Test Activity 2")
        ''')    
        # Insert test words
        cursor.execute('''
            INSERT INTO words (id, kanji, romaji, english) 
            VALUES (1, "食べる", "taberu", "to eat"),
                   (2, "飲む", "nomu", "to drink")
        ''')    
        setup_test_db.commit()
        yield

def test_get_study_sessions(client, app_context):
    """Test listing study sessions"""
    # Create a test session first
    create_data = {"group_id": 1, "study_activity_id": 1}
    client.post('/api/study-sessions', json=create_data)
    
    response = client.get('/api/study-sessions')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data
    assert len(data['items']) > 0
    
def test_create_study_session(client, app_context):
    # Test successful creation of study session
    test_data = {
        "group_id": 1,  # Match the ID from the test data we inserted
        "study_activity_id": 2  # Match the ID from the test data we inserted
    }
    
    # Make POST request
    response = client.post(
        '/api/study-sessions',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    # Print response data for debugging
    print(f"Response 1: {response.data}")
    print(f"Status Code: {response.status_code}")
    
    # Assert response
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'session' in data
    assert data['session']['group_id'] == 1
    assert data['session']['study_activity_id'] == 2

def test_create_study_session_missing_fields(client, app_context):
    # Test with missing fields
    test_data = {
        "group_id": 1
        # missing study_activity_id
    }
    
    response = client.post(
        '/api/study-sessions',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    assert b"Missing required fields" in response.data

def test_create_study_session_invalid_ids(client, app_context):
    # Test with invalid input
    data = {
        "group_id": "invalid",  # Should be integer
        "study_activity_id": 1
    }
    
    response = client.post(
        '/api/study-sessions',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    # Print response data for debugging
    print(f"Response Invalid : {response.data}")
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 400
    
    # Test with non-existent IDs
    test_data = {
        "group_id": 999,  # Invalid ID
        "study_activity_id": 999  # Invalid ID
    }
    
    response = client.post(
        '/api/study-sessions',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    # Print response data for debugging
    print(f"Response 999: {response.data}")
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 404

def test_update_study_session(client, app_context):
    """Test updating an existing study session"""
    # First create a session
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    response = client.post(
        '/api/study-sessions',
        data=json.dumps(create_data),
        content_type='application/json'
    )
    assert response.status_code == 201
    session_id = json.loads(response.data)['session']['id']
    
    # Now update the session
    update_data = {
        "group_id": 1,  # Change group_id
        "study_activity_id": 1  # Using the same activity for this test
    }
    response = client.put(
        f'/api/study-sessions/{session_id}',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'session' in data
    assert data['session']['group_id'] == update_data['group_id']
    assert data['session']['study_activity_id'] == update_data['study_activity_id']


def test_update_session_not_found(client, app_context):
    """Test updating a non-existent session"""
    update_data = {
        "group_id": 999,
        "study_activity_id": 999
    }
    response = client.put(
        '/api/study-sessions/999',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    print(f"Response: {response.data}")
    assert response.status_code == 404
    assert b"Study session not found" in response.data

def test_update_session_invalid_data(client, app_context):
    # First create a study session
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    
    response = client.post(
        '/api/study-sessions',
        json=create_data,
        content_type='application/json'
    )
    
    session_id = json.loads(response.data)['session']['id']
    
    # Test with invalid group_id
    update_data = {
        "group_id": "invalid",  # Should be integer
        "study_activity_id": 1
    }
    
    response = client.put(
        f'/api/study-sessions/{session_id}',
        json=update_data,
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert b"group_id must be an integer" in response.data
    
def test_session_progress(client, app_context):
    """Test updating session progress"""
    # Create a session first
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    response = client.post(
        '/api/study-sessions',
        data=json.dumps(create_data),
        content_type='application/json'
    )
    session_id = json.loads(response.data)['session']['id']
    
    # Add progress data
    progress_data = {
        "word_id": 1,
        "correct": True
    }
    response = client.post(
        f'/api/study-sessions/{session_id}/progress',
        data=json.dumps(progress_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True

def test_session_stats(client, app_context):
    """Test getting session statistics"""
    # Create session and add progress
    create_data = {"group_id": 1, "study_activity_id": 1}
    response = client.post(
        '/api/study-sessions',
        data=json.dumps(create_data),
        content_type='application/json'
    )
    session_id = json.loads(response.data)['session']['id']
    
    # Add two review items
    for word_id in [1, 2]:
        progress_data = {"word_id": word_id, "correct": word_id == 1}
        client.post(
            f'/api/study-sessions/{session_id}/progress',
            data=json.dumps(progress_data),
            content_type='application/json'
        )
    
    # Get stats
    response = client.get(f'/api/study-sessions/{session_id}/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_words' in data
    assert 'correct_words' in data
    assert data['total_words'] == 2
    assert data['correct_words'] == 1
    
def test_update_nonexistent_session(client, app_context):
    """Test updating a session that doesn't exist"""
    response = client.put(
        '/api/study-sessions/999',
        json={
            "group_id": 1,
            "study_activity_id": 1
        }
    )
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "not found" in data["error"]
    
def test_session_progress_invalid_word_id(client, app_context):
    """Test progress update with invalid word_id"""
    # Create a session first
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    response = client.post(
        '/api/study-sessions',
        json=create_data
    )
    session_id = json.loads(response.data)['session']['id']
    
    # Test with invalid word_id type
    progress_data = {
        "word_id": "invalid",
        "correct": True
    }
    response = client.post(
        f'/api/study-sessions/{session_id}/progress',
        json=progress_data
    )
    assert response.status_code == 400
    assert b"word_id must be an integer" in response.data
    
    # Test with non-existent word_id
    progress_data = {
        "word_id": 999999,
        "correct": True
    }
    response = client.post(
        f'/api/study-sessions/{session_id}/progress',
        json=progress_data
    )
    assert response.status_code == 404
    assert b"Word not found" in response.data

def test_session_progress_invalid_correct(client, app_context):
    """Test progress update with invalid correct field"""
    # Create a session first
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    response = client.post(
        '/api/study-sessions',
        json=create_data
    )
    session_id = json.loads(response.data)['session']['id']
    
    # Test with invalid correct type
    progress_data = {
        "word_id": 1,
        "correct": "not_boolean"
    }
    response = client.post(
        f'/api/study-sessions/{session_id}/progress',
        json=progress_data
    )
    assert response.status_code == 400
    assert b"correct must be a boolean" in response.data

def test_get_session_words(client, app_context):
    """Test getting words for a study session"""
    # Create a session first
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    response = client.post(
        '/api/study-sessions',
        json=create_data
    )
    session_id = json.loads(response.data)['session']['id']
    
    # Get words for the session
    response = client.get(f'/api/study-sessions/{session_id}/words')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'words' in data
    assert 'pagination' in data
    assert isinstance(data['words'], list)
    
    # Check pagination structure
    assert 'total_items' in data['pagination']
    assert 'total_pages' in data['pagination']
    assert 'current_page' in data['pagination']
    assert 'per_page' in data['pagination']
    
    # Check word structure if any words exist
    if data['words']:
        word = data['words'][0]
        assert 'id' in word
        assert 'kanji' in word
        assert 'romaji' in word
        assert 'english' in word
        assert 'parts' in word
        assert 'stats' in word
        assert 'correct_count' in word['stats']
        assert 'wrong_count' in word['stats']
        assert 'last_reviewed_at' in word['stats']

def test_get_session_words_nonexistent_session(client, app_context):
    """Test getting words for a non-existent session"""
    response = client.get('/api/study-sessions/999/words')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert "not found" in data["error"].lower()

def test_get_session_words_pagination(client, app_context):
    """Test pagination for session words"""
    # Create a session first
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    response = client.post(
        '/api/study-sessions',
        json=create_data
    )
    session_id = json.loads(response.data)['session']['id']
    
    # Test different page sizes
    response = client.get(f'/api/study-sessions/{session_id}/words?per_page=5')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert len(data['words']) <= 5
    
    # Test page navigation
    response = client.get(f'/api/study-sessions/{session_id}/words?page=2&per_page=5')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['pagination']['current_page'] == 2

def test_get_study_sessions_stats(client, app_context):
    """Test getting study session statistics"""
    # Create a session and add some progress data
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    response = client.post(
        '/api/study-sessions',
        json=create_data
    )
    session_id = json.loads(response.data)['session']['id']
    
    # Add some progress data
    progress_data = [
        {"word_id": 1, "correct": True},
        {"word_id": 2, "correct": False},
        {"word_id": 3, "correct": True}
    ]
    
    for data in progress_data:
        client.post(
            f'/api/study-sessions/{session_id}/progress',
            json=data
        )
    
    # Test different time ranges
    for time_range in ['all', 'today', 'week', 'month']:
        response = client.get(f'/api/study-sessions/stats?range={time_range}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check structure
        assert 'overall' in data
        assert 'by_activity' in data
        assert 'by_group' in data
        assert 'time_range' in data
        
        # Check overall stats
        overall = data['overall']
        assert 'total_sessions' in overall
        assert 'unique_groups' in overall
        assert 'unique_activities' in overall
        assert 'unique_words' in overall
        assert 'total_reviews' in overall
        assert 'correct_reviews' in overall
        assert 'accuracy_rate' in overall
        assert 'last_session_date' in overall
        
        # Check activity stats
        if data['by_activity']:
            activity = data['by_activity'][0]
            assert 'id' in activity
            assert 'name' in activity
            assert 'session_count' in activity
            assert 'words_reviewed' in activity
            assert 'total_reviews' in activity
            assert 'correct_reviews' in activity
            assert 'accuracy_rate' in activity
        
        # Check group stats
        if data['by_group']:
            group = data['by_group'][0]
            assert 'id' in group
            assert 'name' in group
            assert 'session_count' in group
            assert 'words_reviewed' in group
            assert 'total_reviews' in group
            assert 'correct_reviews' in group
            assert 'accuracy_rate' in group

def test_get_study_sessions_stats_invalid_range(client, app_context):
    """Test stats with invalid time range"""
    response = client.get('/api/study-sessions/stats?range=invalid')
    
    assert response.status_code == 200  # Still returns stats for all time
    data = json.loads(response.data)
    assert data['time_range'] == 'all'

def test_review_session(client, app_context):
    """Test reviewing a word in a study session"""
    # Create a session first
    create_data = {
        "group_id": 1,
        "study_activity_id": 1
    }
    response = client.post('/api/study-sessions', json=create_data)
    session_id = json.loads(response.data)['session']['id']
    
    # Test review submission
    review_data = {
        "word_id": 1,
        "correct": True
    }
    
    response = client.post(
        f'/api/study-sessions/{session_id}/review',  # Changed from /progress to /review
        json=review_data
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['message'] == "Review recorded successfully"  # Updated message

def test_review_session_validation(client, app_context):
    """Test validation for session review endpoint"""
    session_id = 1
    
    # Test missing fields
    response = client.post(
        f'/api/study-sessions/{session_id}/review',  # Changed from /progress to /review
        json={}
    )
    assert response.status_code == 400
    
    # Test invalid data types
    response = client.post(
        f'/api/study-sessions/{session_id}/review',  # Changed from /progress to /review
        json={"word_id": "1", "correct": "true"}  # Invalid types
    )
    assert response.status_code == 400


