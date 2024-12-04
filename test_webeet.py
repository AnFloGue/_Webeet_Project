# test_webeet.py

import pytest
import json
from app import app, db, CharacterModel
from flask import url_for
from sqlalchemy import event

@pytest.fixture
def client():
    # Set up a test client
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            seed_test_database()
        yield client
        # Teardown
        with app.app_context():
            db.session.remove()
            db.drop_all()

def seed_test_database():
    # Seed the database with some test data
    characters = [
        CharacterModel(name='Jon Snow', house='Stark', role='King in the North', age=25, strength='Swordsmanship'),
        CharacterModel(name='Daenerys Targaryen', house='Targaryen', role='Queen', age=24, strength='Dragons'),
        CharacterModel(name='Arya Stark', house='Stark', role='Assassin', age=18, strength='Stealth'),
        CharacterModel(name='Cersei Lannister', house='Lannister', role='Queen', age=42, strength='Politics'),
        CharacterModel(name='Tyrion Lannister', house='Lannister', role='Hand of the Queen', age=39, strength='Intelligence'),
    ]
    db.session.bulk_save_objects(characters)
    db.session.commit()

def test_get_all_characters(client):
    response = client.get('/characters')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) <= 20  # Should return up to 20 random characters

def test_pagination(client):
    response = client.get('/characters?limit=2&skip=1')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2

def test_get_character_by_id(client):
    response = client.get('/characters/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Jon Snow'

def test_get_character_by_invalid_id(client):
    response = client.get('/characters/999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_filter_characters_case_insensitive(client):
    response = client.get('/characters?house=stark')
    assert response.status_code == 200
    data_lower = response.get_json()
    response = client.get('/characters?house=STArk')
    assert response.status_code == 200
    data_mixed = response.get_json()
    assert data_lower == data_mixed  # Should be the same due to case-insensitive filtering

def test_filter_characters_by_age_range(client):
    response = client.get('/characters?age_more_than=20&age_less_than=30')
    assert response.status_code == 200
    data = response.get_json()
    for character in data:
        assert 20 <= character['age'] <= 30

def test_filter_and_sort_combined(client):
    response = client.get('/characters?house=stark&sort_by=age&order=asc')
    assert response.status_code == 200
    data = response.get_json()
    ages = [character['age'] for character in data]
    assert ages == sorted(ages)
    for character in data:
        assert character['house'].lower() == 'stark'

def test_add_new_character(client):
    new_character = {
        "name": "Bran Stark",
        "house": "Stark",
        "role": "Three-Eyed Raven",
        "age": 17,
        "strength": "Greensight"
    }
    response = client.post('/characters', json=new_character)
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data

    # Verify that the character was added
    response = client.get(f'/characters/{data["id"]}')
    assert response.status_code == 200
    character_data = response.get_json()
    assert character_data['name'] == new_character['name']

def test_add_character_missing_fields(client):
    incomplete_character = {
        "name": "Ghost",
        "age": 5
    }
    response = client.post('/characters', json=incomplete_character)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_edit_character(client):
    update_data = {
        "nickname": "The Imp",
        "strength": "Wit"
    }
    response = client.patch('/characters/5', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Character updated'

    # Verify the update
    response = client.get('/characters/5')
    assert response.status_code == 200
    character_data = response.get_json()
    assert character_data['nickname'] == 'The Imp'
    assert character_data['strength'] == 'Wit'

def test_edit_nonexistent_character(client):
    update_data = {
        "nickname": "No One"
    }
    response = client.patch('/characters/999', json=update_data)
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_delete_character(client):
    response = client.delete('/characters/3')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Character deleted'

    # Verify deletion
    response = client.get('/characters/3')
    assert response.status_code == 404

def test_delete_nonexistent_character(client):
    response = client.delete('/characters/999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_invalid_http_method(client):
    response = client.put('/characters/1', json={})
    assert response.status_code == 405  # Method Not Allowed

def test_invalid_filter_attribute(client):
    response = client.get('/characters?height=180')
    assert response