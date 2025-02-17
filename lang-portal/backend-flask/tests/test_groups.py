import pytest
import json
from flask import g

def test_create_group(client, app_context):
    """Test creating a new group"""
    test_name = 'Test Group Creation'
    response = client.post('/api/groups', json={'name': test_name})
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data
    assert 'name' in data
    assert data['name'] == test_name
    assert 'words_count' in data
    assert data['words_count'] == 0

def test_get_group_words_raw(client, app_context):
    """Test getting raw words data for a group"""
    # Create a group
    group_data = {"name": "Test Group Raw"}
    response = client.post('/api/groups', json=group_data)
    assert response.status_code == 201
    group_id = json.loads(response.data)['id']
    
    # Add test words
    with app_context:
        cursor = g.db.cursor()
        cursor.execute('''
            INSERT INTO words (kanji, english, romaji, parts) 
            VALUES 
            ("猫", "cat", "neko", "noun"),
            ("犬", "dog", "inu", "noun")
        ''')
        g.db.commit()
        
        # Get the inserted word IDs
        cursor.execute('SELECT id FROM words ORDER BY id DESC LIMIT 2')
        word_ids = [row[0] for row in cursor.fetchall()]
        
        # Link words to group
        for word_id in word_ids:
            cursor.execute('''
                INSERT INTO word_groups (group_id, word_id) 
                VALUES (?, ?)
            ''', (group_id, word_id))
        g.db.commit()
    
    # Test getting raw words
    response = client.get(f'/api/groups/{group_id}/words/raw')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'words' in data
    assert 'count' in data
    assert data['count'] == 2
    
    words = data['words']
    assert len(words) == 2
    for word in words:
        assert all(key in word for key in [
            'id', 'kanji', 'english', 'romaji', 
            'parts'
        ]) 