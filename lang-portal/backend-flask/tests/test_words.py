import pytest
import json
from flask import g

def test_get_words_pagination(client, app_context):
    """Test words pagination and sorting"""
    # Add test words
    with app_context:
        try:
            cursor = g.db.cursor()
            cursor.execute('''
                INSERT INTO words (kanji, english, romaji, parts) 
                VALUES (?, ?, ?, ?)
            ''', ("猫", "cat", "neko", "noun"))
            cursor.execute('''
                INSERT INTO words (kanji, english, romaji, parts) 
                VALUES (?, ?, ?, ?)
            ''', ("犬", "dog", "inu", "noun"))
            cursor.execute('''
                INSERT INTO words (kanji, english, romaji, parts) 
                VALUES (?, ?, ?, ?)
            ''', ("魚", "fish", "sakana", "noun"))
            g.db.commit()
        except Exception as e:
            g.db.rollback()
            pytest.fail(f"Database operation failed: {str(e)}")
    
    # Test default pagination
    response = client.get('/api/words')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'words' in data
    assert 'pagination' in data
    assert data['pagination']['current_page'] == 1
    assert len(data['words']) <= data['pagination']['per_page']
    
def test_invalid_parameters(client, app_context):
    """Test handling of invalid query parameters"""
    # Test invalid sort field
    response = client.get('/api/words?sort_by=invalid')
    assert response.status_code == 200  # Should default to kanji
    
    # Test invalid order
    response = client.get('/api/words?order=invalid')
    assert response.status_code == 200  # Should default to ASC
    
    # Test invalid page number
    response = client.get('/api/words?page=0')
    assert response.status_code == 200  # Should default to page 1

def test_get_single_word(client, app_context):
    """Test getting a single word by ID"""
    # Add test word
    with app_context:
        try:
            cursor = g.db.cursor()
            cursor.execute('''
                INSERT INTO words (kanji, english, romaji, parts) 
                VALUES (?, ?, ?, ?)
            ''', ("猫", "cat", "neko", "noun"))
            g.db.commit()
            word_id = cursor.lastrowid
        except Exception as e:
            g.db.rollback()
            pytest.fail(f"Database operation failed: {str(e)}")
    
    # Test getting existing word
    response = client.get(f'/api/words/{word_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['word']['kanji'] == "猫"
    
    # Test getting non-existent word
    response = client.get('/api/words/999999')
    assert response.status_code == 404
      
@pytest.fixture
def cleanup(client):
    """Fixture to clean up test data after each test"""
    yield
    with client.application.app_context():
        cursor = g.db.cursor()
        cursor.execute('DELETE FROM word_review_items')
        cursor.execute('DELETE FROM words')
        g.db.commit()