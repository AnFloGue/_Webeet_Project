import unittest
import json
from app import app

class CharacterAPITestCase(unittest.TestCase):
    """
    Test case for the Character API.
    """

    def setUp(self):
        """
        Set up the test client before each test.
        """
        self.client = app.test_client()
        self.client.testing = True

    def test_get_characters(self):
        """
        Test the GET /characters endpoint.
        This test checks if the endpoint returns up to 20 random characters.
        """
        response = self.client.get('/characters')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertLessEqual(len(data), 20)
    
    def test_pagination(self):
        """
        Test the GET /characters endpoint with pagination.
        This test checks if the endpoint returns the correct number of characters with limit and skip parameters.
        """
        response = self.client.get('/characters?limit=2&skip=1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 2)
    
    def test_get_character_by_id(self):
        """
        Test the GET /characters/<id> endpoint.
        This test checks if the endpoint returns the correct character by ID.
        """
        response = self.client.get('/characters/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['name'], 'Jon Snow')
    
    def test_get_character_by_invalid_id(self):
        """
        Test the GET /characters/<id> endpoint with an invalid ID.
        This test checks if the endpoint returns a 404 error for a non-existent character.
        """
        response = self.client.get('/characters/999')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_filter_characters_case_insensitive(self):
        """
        Test the GET /characters endpoint with case-insensitive filtering.
        """
        # Make two requests with different case but same content
        response_lower = self.client.get('/characters?name=tyrion&sort_by=id')
        response_mixed = self.client.get('/characters?name=TyRiOn&sort_by=id')
        
        # Check status codes
        self.assertEqual(response_lower.status_code, 200)
        self.assertEqual(response_mixed.status_code, 200)
        
        # Compare the data
        data_lower = json.loads(response_lower.data)
        data_mixed = json.loads(response_mixed.data)
        
        # The responses should be identical regardless of case
        self.assertEqual(data_lower, data_mixed)
    
    def test_filter_characters_by_age_range(self):
        """
        Test the GET /characters endpoint with age range filtering.
        This test checks if the endpoint returns characters within the specified age range.
        """
        response = self.client.get('/characters?age_more_than=20&age_less_than=30')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for character in data:
            self.assertTrue(20 <= character['age'] <= 30)
    
    def test_filter_and_sort_combined(self):
        """
        Test the GET /characters endpoint with combined filtering and sorting.
        This test checks if the endpoint returns correctly filtered and sorted characters.
        """
        response = self.client.get('/characters?house=stark&sort_by=age&order=asc')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        ages = [character['age'] for character in data]
        self.assertEqual(ages, sorted(ages))
        for character in data:
            self.assertEqual(character['house'].lower(), 'stark')
    
    def test_add_new_character(self):
        """
        Test the POST /characters endpoint.
        This test checks if a new character can be added to the database.
        """
        new_character = {
            "name": "Bran Stark",
            "house": "Stark",
            "role": "Three-Eyed Raven",
            "age": 17,
            "strength": "Greensight"
        }
        response = self.client.post('/characters', json=new_character)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)
        
        response = self.client.get(f'/characters/{data["id"]}')
        self.assertEqual(response.status_code, 200)
        character_data = response.get_json()
        self.assertEqual(character_data['name'], new_character['name'])
    
    def test_add_character_missing_fields(self):
        """
        Test the POST /characters endpoint with missing fields.
        This test checks if the endpoint returns a 400 error for missing required fields.
        """
        incomplete_character = {
            "name": "Ghost",
            "age": 5
        }
        response = self.client.post('/characters', json=incomplete_character)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_edit_character(self):
        """
        Test the PATCH /characters/<id> endpoint.
        This test checks if an existing character can be updated.
        """
        update_data = {
            "nickname": "The Imp",
            "strength": "Wit"
        }
        response = self.client.patch('/characters/5', json=update_data)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Character updated')
        
        response = self.client.get('/characters/5')
        self.assertEqual(response.status_code, 200)
        character_data = response.get_json()
        self.assertEqual(character_data['nickname'], 'The Imp')
        self.assertEqual(character_data['strength'], 'Wit')
    
    def test_edit_nonexistent_character(self):
        """
        Test the PATCH /characters/<id> endpoint with a non-existent character.
        This test checks if the endpoint returns a 404 error for a non-existent character.
        """
        update_data = {
            "nickname": "No One"
        }
        response = self.client.patch('/characters/999', json=update_data)
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)
    
    
    
    
    def test_delete_nonexistent_character(self):
        """
        Test the DELETE /characters/<id> endpoint with a non-existent character.
        This test checks if the endpoint returns a 404 error for a non-existent character.
        """
        response = self.client.delete('/characters/999')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_invalid_http_method(self):
        """
        Test an invalid HTTP method on the /characters/<id> endpoint.
        This test checks if the endpoint returns a 405 error for an unsupported HTTP method.
        """
        response = self.client.put('/characters/1', json={})
        self.assertEqual(response.status_code, 405)
    
    def test_invalid_filter_attribute(self):
        """
        Test the GET /characters endpoint with an invalid filter attribute.
        This test checks if the endpoint returns a 400 error for an invalid filter attribute.
        """
        response = self.client.get('/characters?height=180')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        
    def test_delete_last_character(self):
        """
        Test the DELETE /characters/<id> endpoint.
        This test checks if the last character can be deleted.
        """
        # Retrieve the list of characters
        response = self.client.get('/characters')
        self.assertEqual(response.status_code, 200)
        characters = response.get_json()
        
        # Get the last character's ID
        last_character_id = characters[-1]['id']
        
        # Attempt to delete the last character
        response = self.client.delete(f'/characters/{last_character_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Character deleted')
        
        # Verify the character has been deleted
        response = self.client.get(f'/characters/{last_character_id}')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()