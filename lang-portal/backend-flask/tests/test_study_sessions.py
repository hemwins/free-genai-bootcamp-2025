import pytest
import json
from datetime import datetime

def test_create_study_session(client, app_context):
    """Test creating a new study session"""
    # Create a group first
    group_response = client.post('/api/groups', json={'name': 'Test Group'})
    group_id = json.loads(group_response.data)['id']
    
    # Create study activity
    activity_data = {
        'name': 'Test Activity',
        'description': 'Test Description'
    }
    activity_response = client.post('/api/study-activities', json=activity_data)
    activity_id = json.loads(activity_response.data)['id']
    
    # Create study session
    session_data = {
        'group_id': group_id,
        'study_activity_id': activity_id
    }
    response = client.post('/api/study-sessions', json=session_data)
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data
    assert data['group_id'] == group_id
    assert data['study_activity_id'] == activity_id
    assert 'start_time' in data

def test_get_study_session(client, app_context):
    """Test getting a study session"""
    # Create prerequisites and session
    group_response = client.post('/api/groups', json={'name': 'Test Group'})
    group_id = json.loads(group_response.data)['id']
    
    activity_response = client.post('/api/study-activities', 
                                  json={'name': 'Test Activity'})
    activity_id = json.loads(activity_response.data)['id']
    
    session_response = client.post('/api/study-sessions', 
                                 json={'group_id': group_id, 
                                      'study_activity_id': activity_id})
    session_id = json.loads(session_response.data)['id']
    
    # Test getting the session
    response = client.get(f'/api/study-sessions/{session_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['session']['id'] == session_id
    assert data['session']['group_id'] == group_id
    assert data['session']['study_activity_id'] == activity_id
    assert 'start_time' in data['session'] 