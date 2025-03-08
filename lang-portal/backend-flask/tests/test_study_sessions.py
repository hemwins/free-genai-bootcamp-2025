import pytest
import json
from datetime import datetime

@pytest.fixture
def cleanup(client):
    """Fixture to clean up test data after each test"""
    yield
    # Delete all study sessions, activities and groups created during tests
    client.delete('/api/study-sessions')
    client.delete('/api/study-activities')
    client.delete('/api/groups')

@pytest.fixture
def study_prerequisites(client):
    """Create group and activity prerequisites for tests"""
    # Create a group
    group_response = client.post('/api/groups', json={'name': 'Test Group'})
    group_id = json.loads(group_response.data)['id']
    
    # Create study activity
    activity_data = {
        'name': 'Test Activity',
        'description': 'Test Description'
    }
    activity_response = client.post('/api/study-activities', json=activity_data)
    activity_id = json.loads(activity_response.data)['id']
    
    return {'group_id': group_id, 'activity_id': activity_id}

def test_create_study_session(client, app_context, cleanup, study_prerequisites):
    """Test creating a new study session"""
    # Create study session using prerequisites
    session_data = {
        'group_id': study_prerequisites['group_id'],
        'study_activity_id': study_prerequisites['activity_id']
    }
    response = client.post('/api/study-sessions', json=session_data)
    
    assert response.status_code == 201
    data = json.loads(response.data)['session']
    assert 'id' in data
    assert isinstance(data['id'], int)
    assert data['group_id'] == study_prerequisites['group_id']
    assert data['study_activity_id'] == study_prerequisites['activity_id']
    assert 'start_time' in data
    # Validate timestamp format
    start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
    assert isinstance(start_time, datetime)

def test_get_study_session(client, app_context, cleanup, study_prerequisites):
    """Test getting a study session"""
    # Create session using prerequisites
    session_data = {
        'group_id': study_prerequisites['group_id'],
        'study_activity_id': study_prerequisites['activity_id']
    }
    session_response = client.post('/api/study-sessions', json=session_data)
    session_id = json.loads(session_response.data)['session']['id']
    
    # Test getting the session
    response = client.get(f'/api/study-sessions/{session_id}')
    assert response.status_code == 200
    data = json.loads(response.data)['session']
    
    assert data['id'] == session_id
    assert isinstance(data['id'], int)
    assert data['group_id'] == study_prerequisites['group_id']
    assert data['study_activity_id'] == study_prerequisites['activity_id']
    assert 'start_time' in data
    # Validate timestamp format
    start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
    assert isinstance(start_time, datetime)

def test_create_study_session_invalid_data(client, app_context, cleanup):
    """Test creating a study session with invalid data"""
    # Test with non-existent group_id
    session_data = {
        'group_id': 9999,
        'study_activity_id': 1
    }
    response = client.post('/api/study-sessions', json=session_data)
    assert response.status_code == 404
    
    # Test with non-existent activity_id
    group_response = client.post('/api/groups', json={'name': 'Test Group'})
    group_id = json.loads(group_response.data)['id']
    
    session_data = {
        'group_id': group_id,
        'study_activity_id': 9999
    }
    response = client.post('/api/study-sessions', json=session_data)
    assert response.status_code == 404