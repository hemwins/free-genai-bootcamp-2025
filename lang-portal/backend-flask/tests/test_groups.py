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

@pytest.fixture
def test_words(app_context):
    """Fixture to create test words and return their IDs"""
    try:
        with app_context:
            with app_context.app.db.get() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO words (kanji, english, romaji, parts) 
                        VALUES 
                        ("猫", "cat", "neko", "noun"),
                        ("犬", "dog", "inu", "noun")
                    ''')
                except Exception as e:
                    pytest.fail(f"Failed to insert test words: {e}")
                conn.commit()
                
                try:
                    cursor.execute('SELECT id FROM words ORDER BY id DESC LIMIT 2')
                    return [row[0] for row in cursor.fetchall()]
                except Exception as e:
                    pytest.fail(f"Failed to retrieve word IDs: {e}")
    except Exception as e:
        pytest.fail(f"Database operation failed: {e}")
        
def test_get_groups_pagination_sorting(client, app_context):
    """Test getting groups with pagination and sorting"""
    # Create test groups
    group_names = ["A Group", "B Group", "C Group"]
    for name in group_names:
        response = client.post('/api/groups', json={'name': name})
        assert response.status_code == 201
    
    # Test default pagination
    response = client.get('/api/groups')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'groups' in data
    assert 'total_pages' in data
    assert 'current_page' in data
    
    # Test sorting by name
    response = client.get('/api/groups?sort_by=name&order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    groups = data['groups']
    assert groups[0]['group_name'] > groups[1]['group_name']
    
    # Test sorting by word count
    response = client.get('/api/groups?sort_by=words_count&order=asc')
    assert response.status_code == 200
    
def test_get_single_group(client, app_context):
    """Test getting a single group by ID"""
    # Create a test group
    group_data = {"name": "Test Single Group"}
    create_response = client.post('/api/groups', json=group_data)
    group_id = json.loads(create_response.data)['id']
    
    # Test getting existing group
    response = client.get(f'/api/groups/{group_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == group_id
    assert data['group_name'] == group_data['name']
    
    # Test getting non-existent group
    response = client.get('/api/groups/99999')
    assert response.status_code == 404
    
def test_update_group(client, app_context):
    """Test updating a group"""
    # Create initial group
    group_data = {"name": "Original Name"}
    create_response = client.post('/api/groups', json=group_data)
    group_id = json.loads(create_response.data)['id']
    
    # Test updating name
    update_data = {"name": "Updated Name"}
    response = client.put(f'/api/groups/{group_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['group']['name'] == update_data['name']
    
    # Test updating non-existent group
    response = client.put('/api/groups/99999', json=update_data)
    assert response.status_code == 404
    
    # Test updating with existing name
    client.post('/api/groups', json={"name": "Existing Name"})
    response = client.put(f'/api/groups/{group_id}', 
                         json={"name": "Existing Name"})
    assert response.status_code == 409

def test_get_group_words_raw(client, app_context, test_words):
    """Test getting raw words data for a group"""
    # Create a group
    group_data = {"name": "Test Group Raw"}
    response = client.post('/api/groups', json=group_data)
    assert response.status_code == 201
    group_id = json.loads(response.data)['id']
    
    word_ids = test_words
    try:
        # Link words to group
        try:
            with app_context:
                with app_context.app.db.get() as conn:
                    cursor = conn.cursor()
                    for word_id in word_ids:
                        try:
                            cursor.execute('''
                                INSERT INTO word_groups (group_id, word_id) 
                                VALUES (?, ?)
                            ''', (group_id, word_id))
                        except Exception as e:
                            pytest.fail(f"Failed to insert word_group: {e}")
                    conn.commit()
        except Exception as e:
            pytest.fail(f"Database operation failed: {e}")
        
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
    finally:
        # Clean up test data
        try:
            with app_context:
                with app_context.app.db.get() as conn:
                    cursor = conn.cursor()
                    try:
                        for word_id in word_ids:
                            cursor.execute('DELETE FROM word_groups WHERE word_id = ?', (word_id,))
                        cursor.execute('DELETE FROM words WHERE id IN ({})'.format(','.join('?' * len(word_ids))), word_ids)
                        cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
                    except Exception as e:
                        pytest.fail(f"Failed to clean up test data: {e}")
                    conn.commit()
        except Exception as e:
            pytest.fail(f"Database cleanup operation failed: {e}")