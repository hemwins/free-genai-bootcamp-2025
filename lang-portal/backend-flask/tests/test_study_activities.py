import pytest
import json
from flask import g

def test_get_study_activities(client, app_context):
    """Test getting all study activities"""
    # Create some test activities
    activities = [
        {'name': 'Test Activity 1', 'url': 'http://test1.com'},
        {'name': 'Test Activity 2', 'url': 'http://test2.com'}
    ]
    
    for activity in activities:
        client.post('/api/study-activities', json=activity)
    
    response = client.get('/api/study-activities')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'activities' in data
    assert len(data['activities']) >= len(activities)
    
    # Verify structure of returned activities
    for activity in data['activities']:
        assert 'id' in activity
        assert 'name' in activity
        assert 'url' in activity
        assert 'session_count' in activity
        assert 'last_used_at' in activity

def test_create_study_activity(client, app_context):
    """Test creating a new study activity"""
    activity_data = {
        'name': 'Test Activity',
        'url': 'http://test.com',
        'preview_url': 'http://test.com/preview'
    }
    
    response = client.post('/api/study-activities', json=activity_data)
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'activity' in data
    assert data['activity']['name'] == activity_data['name']
    assert data['activity']['url'] == activity_data['url']
    assert data['activity']['preview_url'] == activity_data['preview_url']

def test_create_activity_duplicate_name(client, app_context):
    """Test creating an activity with duplicate name"""
    activity_data = {
        'name': 'Duplicate Activity',
        'url': 'http://test.com'
    }
    
    # Create first activity
    client.post('/api/study-activities', json=activity_data)
    
    # Try to create duplicate
    response = client.post('/api/study-activities', json=activity_data)
    
    assert response.status_code == 409
    assert b"already exists" in response.data

def test_update_study_activity(client, app_context):
    """Test updating a study activity"""
    # Create activity first
    activity_data = {
        'name': 'Original Name',
        'url': 'http://original.com'
    }
    
    response = client.post('/api/study-activities', json=activity_data)
    activity_id = json.loads(response.data)['activity']['id']
    
    # Update activity
    update_data = {
        'name': 'Updated Name',
        'url': 'http://updated.com'
    }
    
    response = client.put(f'/api/study-activities/{activity_id}', json=update_data)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['activity']['name'] == update_data['name']
    assert data['activity']['url'] == update_data['url']

def test_delete_study_activity(client, app_context):
    """Test deleting a study activity"""
    # Create activity first
    activity_data = {
        'name': 'Activity to Delete',
        'url': 'http://delete.com'
    }
    
    response = client.post('/api/study-activities', json=activity_data)
    activity_id = json.loads(response.data)['activity']['id']
    
    # Delete activity
    response = client.delete(f'/api/study-activities/{activity_id}')
    assert response.status_code == 204
    
    # Verify deletion
    response = client.get(f'/api/study-activities/{activity_id}')
    assert response.status_code == 404

def test_activity_validation(client, app_context):
    """Test activity input validation"""
    # Test missing required fields
    response = client.post('/api/study-activities', json={'name': 'Test'})
    assert response.status_code == 400
    
    # Test invalid field types
    response = client.post('/api/study-activities', 
                          json={'name': 123, 'url': 'http://test.com'})
    assert response.status_code == 400
    
    # Test non-existent activity
    response = client.put('/api/study-activities/999', 
                         json={'name': 'New Name'})
    assert response.status_code == 404 