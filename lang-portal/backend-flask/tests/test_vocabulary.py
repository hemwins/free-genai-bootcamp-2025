import pytest
import json
from flask import g

    
def test_post_vocabulary_invalid_format(client, app_context):
    """Test posting vocabulary with invalid data format"""
    # Test missing required fields in vocabulary item
    vocabulary_data = {
        "category": "Test Category",
        "data": [
            {
                "kanji": "猫",  # Missing romaji and english
            }
        ]
    }
    response = client.post('/api/vocabulary', json=vocabulary_data)
    assert response.status_code == 400
    
    # Test invalid data types
    vocabulary_data = {
        "category": "Test Category",
        "data": [
            {
                "kanji": 123,  # Should be string
                "romaji": "neko",
                "english": "cat",
                "parts": "invalid"  # Should be array
            }
        ]
    }
    response = client.post('/api/vocabulary', json=vocabulary_data)
    assert response.status_code == 400
    
def test_post_vocabulary_empty_data(client, app_context):
    """Test posting empty vocabulary data"""
    vocabulary_data = {
        "category": "Test Category",
        "data": []
    }
    response = client.post('/api/vocabulary', json=vocabulary_data)
    assert response.status_code == 400
    
def test_post_vocabulary_missing_data(client, app_context):
    """Test posting vocabulary with missing required data"""
    # Test missing category
    response = client.post('/api/vocabulary', json={"data": []})
    assert response.status_code == 400
    
    # Test missing vocabulary data
    response = client.post('/api/vocabulary', json={"category": "Test"})
    assert response.status_code == 400


@pytest.fixture
def cleanup(client):
    """Fixture to clean up test data after each test"""
    yield
    # Clean up test data
    with client.application.app_context():
        cursor = g.db.cursor()
        cursor.execute('DELETE FROM word_groups')
        cursor.execute('DELETE FROM words')
        cursor.execute('DELETE FROM groups')
        g.db.commit()