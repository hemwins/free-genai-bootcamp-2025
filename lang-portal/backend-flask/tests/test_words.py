import json

def test_get_words_default_params(client, app_context):
    """Test getting words with default parameters"""
    response = client.get('/api/words')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Check response structure
    assert all(key in data for key in ['words', 'pagination', 'sorting'])
    assert all(key in data['pagination'] for key in 
              ['total_items', 'total_pages', 'current_page', 'per_page'])
    assert all(key in data['sorting'] for key in ['sort_by', 'order'])
    
    # Check default values
    assert data['pagination']['current_page'] == 1
    assert data['pagination']['per_page'] == 50
    assert data['sorting']['sort_by'] == 'kanji'
    assert data['sorting']['order'] == 'asc'

def test_get_words_with_sorting(client, app_context):
    """Test getting words with different sorting parameters"""
    sort_fields = ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']
    orders = ['asc', 'desc']
    
    for sort_by in sort_fields:
        for order in orders:
            response = client.get(f'/api/words?sort_by={sort_by}&order={order}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['sorting']['sort_by'] == sort_by
            assert data['sorting']['order'] == order

def test_get_words_pagination(client, app_context):
    """Test words pagination"""
    # Get first page
    response = client.get('/api/words?page=1&per_page=10')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['words']) <= 10
    
    # Get second page
    response = client.get('/api/words?page=2&per_page=10')
    assert response.status_code == 200
    data2 = json.loads(response.data)
    
    # Ensure different pages return different words
    if len(data['words']) == 10 and len(data2['words']) > 0:
        assert data['words'][0]['id'] != data2['words'][0]['id']

def test_get_words_invalid_params(client, app_context):
    """Test words endpoint with invalid parameters"""
    # Invalid sort field
    response = client.get('/api/words?sort_by=invalid')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['sorting']['sort_by'] == 'kanji'  # Should default to kanji
    
    # Invalid order
    response = client.get('/api/words?order=invalid')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['sorting']['order'] == 'asc'  # Should default to asc

def test_words_data_structure(client, app_context):
    """Test the structure of returned word data"""
    response = client.get('/api/words')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    if len(data['words']) > 0:
        word = data['words'][0]
        assert all(key in word for key in [
            'id', 'kanji', 'romaji', 'english', 
            'part_of_speech', 'level', 'stats', 'groups'
        ])
        assert all(key in word['stats'] for key in [
            'correct_count', 'wrong_count', 'accuracy', 'last_reviewed'
        ]) 