import pytest
import json
from flask import g

def test_get_words_pagination(client, app_context):
    """Test words pagination and sorting"""
    # Add test words
    with app_context:
        cursor = g.db.cursor()
        cursor.execute('''
            INSERT INTO words (kanji, english, romaji, parts) 
            VALUES 
            ("猫", "cat", "neko", "noun"),
            ("犬", "dog", "inu", "noun"),
            ("魚", "fish", "sakana", "noun")
        ''')
        g.db.commit()
    
    # Test default pagination
    response = client.get('/api/words')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'words' in data
    assert 'pagination' in data
    assert data['pagination']['current_page'] == 1
    assert len(data['words']) <= data['pagination']['per_page']

def test_word_search(client, app_context):
    """Test word search functionality"""
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
    
    # Test search by kanji
    response = client.get('/api/words?search=猫')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['words']) == 1
    assert data['words'][0]['kanji'] == '猫'
    
    # Test search by english
    response = client.get('/api/words?search=dog')
    data = json.loads(response.data)
    assert len(data['words']) == 1
    assert data['words'][0]['english'] == 'dog' 