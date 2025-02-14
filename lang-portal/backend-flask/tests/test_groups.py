import pytest
import json
import logging
from flask import g

# Setup test logger
logger = logging.getLogger(__name__)

def test_create_group(client, app_context):
    """Test creating a new group"""
    logger.info("Starting test: create_group")
    
    test_name = 'Test Group Creation'
    logger.debug(f"Attempting to create group: {test_name}")
    
    response = client.post(
        '/api/groups',
        json={'name': test_name}
    )
    
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response data: {response.data}")
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'group' in data
    assert data['group']['name'] == test_name
    assert 'word_count' in data['group']
    assert 'session_count' in data['group']
    
    logger.info("Successfully completed create_group test")

def test_create_group_duplicate_name(client, app_context):
    """Test creating a group with duplicate name"""
    logger.info("Starting test: create_group_duplicate_name")
    
    test_name = 'Duplicate Group'
    logger.debug(f"Creating first group: {test_name}")
    
    # Create first group
    response = client.post('/api/groups', json={'name': test_name})
    assert response.status_code == 201
    
    logger.debug("Attempting to create duplicate group")
    # Try to create group with same name
    response = client.post('/api/groups', json={'name': test_name})
    
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response data: {response.data}")
    
    assert response.status_code == 409
    assert b"already exists" in response.data
    
    logger.info("Successfully completed duplicate name test")

def test_update_group(client, app_context):
    """Test updating a group"""
    logger.info("Starting test: update_group")
    
    # Create a group first
    original_name = 'Original Name'
    updated_name = 'Updated Name'
    
    logger.debug(f"Creating group with name: {original_name}")
    response = client.post('/api/groups', json={'name': original_name})
    group_id = json.loads(response.data)['group']['id']
    
    logger.debug(f"Updating group {group_id} with name: {updated_name}")
    # Update the group
    response = client.put(
        f'/api/groups/{group_id}',
        json={'name': updated_name}
    )
    
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response data: {response.data}")
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['group']['name'] == updated_name
    
    logger.info("Successfully completed update_group test")

def test_delete_group(client, app_context):
    """Test deleting a group"""
    logger.info("Starting test: delete_group")
    
    # Create a group first
    test_name = 'Group to Delete'
    logger.debug(f"Creating group: {test_name}")
    
    response = client.post('/api/groups', json={'name': test_name})
    group_id = json.loads(response.data)['group']['id']
    
    logger.debug(f"Attempting to delete group: {group_id}")
    # Delete the group
    response = client.delete(f'/api/groups/{group_id}')
    
    logger.debug(f"Delete response status: {response.status_code}")
    assert response.status_code == 204
    
    # Verify group is deleted
    logger.debug(f"Verifying group {group_id} is deleted")
    response = client.get(f'/api/groups/{group_id}')
    assert response.status_code == 404
    
    logger.info("Successfully completed delete_group test")

def test_get_groups_pagination(client, app_context):
    """Test groups pagination"""
    logger.info("Starting test: get_groups_pagination")
    
    # Create multiple groups
    logger.debug("Creating 15 test groups")
    for i in range(15):
        client.post('/api/groups', json={'name': f'Test Group {i}'})
    
    # Test default pagination
    logger.debug("Testing default pagination")
    response = client.get('/api/groups')
    data = json.loads(response.data)
    assert 'pagination' in data
    assert len(data['groups']) <= 10  # default per_page
    
    # Test custom pagination
    logger.debug("Testing custom pagination (page=2, per_page=5)")
    response = client.get('/api/groups?page=2&per_page=5')
    data = json.loads(response.data)
    assert len(data['groups']) <= 5
    assert data['pagination']['current_page'] == 2
    
    logger.info("Successfully completed pagination test")

def test_group_not_found(client, app_context):
    """Test operations with non-existent group"""
    logger.info("Starting test: group_not_found")
    
    non_existent_id = 999
    logger.debug(f"Testing GET with non-existent ID: {non_existent_id}")
    response = client.get(f'/api/groups/{non_existent_id}')
    assert response.status_code == 404
    
    logger.debug(f"Testing PUT with non-existent ID: {non_existent_id}")
    response = client.put(f'/api/groups/{non_existent_id}', json={'name': 'New Name'})
    assert response.status_code == 404
    
    logger.debug(f"Testing DELETE with non-existent ID: {non_existent_id}")
    response = client.delete(f'/api/groups/{non_existent_id}')
    assert response.status_code == 404
    
    logger.info("Successfully completed not_found tests")

def test_get_group_words_raw(client, app_context):
    """Test getting raw words data for a group"""
    # First create a group and add some words
    group_data = {"name": "Test Group Raw"}
    response = client.post('/api/groups', json=group_data)
    assert response.status_code == 201
    group_id = json.loads(response.data)['group']['id']
    
    # Add some words to the group (assuming you have a way to add words)
    # This might need to be done directly in the database for testing
    with app_context:
        cursor = app_context.cursor()
        # Add test words
        cursor.execute('''
            INSERT INTO words (kanji, english, romaji, part_of_speech, level) 
            VALUES 
            ("猫", "cat", "neko", "noun", "N5"),
            ("犬", "dog", "inu", "noun", "N5")
        ''')
        word_ids = [cursor.lastrowid, cursor.lastrowid + 1]
        
        # Link words to group
        for word_id in word_ids:
            cursor.execute('''
                INSERT INTO word_groups (group_id, word_id) 
                VALUES (?, ?)
            ''', (group_id, word_id))
        app_context.commit()
    
    # Test getting raw words
    response = client.get(f'/api/groups/{group_id}/words/raw')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify response structure
    assert 'words' in data
    assert 'count' in data
    assert data['count'] == 2
    
    # Verify word data
    words = data['words']
    assert len(words) == 2
    for word in words:
        assert all(key in word for key in [
            'id', 'kanji', 'english', 'romaji', 
            'part_of_speech', 'level', 'added_at'
        ])

def test_get_group_words_raw_not_found(client, app_context):
    """Test getting raw words for non-existent group"""
    response = client.get('/api/groups/999/words/raw')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "not found" in data["error"].lower()

def test_get_group_words_raw_empty(client, app_context):
    """Test getting raw words for empty group"""
    # Create empty group
    group_data = {"name": "Empty Group"}
    response = client.post('/api/groups', json=group_data)
    group_id = json.loads(response.data)['group']['id']
    
    # Test getting words
    response = client.get(f'/api/groups/{group_id}/words/raw')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['count'] == 0
    assert len(data['words']) == 0 