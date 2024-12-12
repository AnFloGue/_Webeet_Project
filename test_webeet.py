# test_webeet.py
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
        # The response should contain up to 20 characters
        self.assertLessEqual(len(data), 20)

    def test_pagination(self):
        """
        Test the GET /characters endpoint with pagination.
        This test checks if the endpoint returns the correct number of characters with limit and skip parameters.
        """
        # Ensure the database has enough characters for pagination
        response = self.client.get('/characters')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        if len(data) < 3:
            self.skipTest("Not enough characters in the database to test pagination")

        # Test pagination with limit=2 and skip=1
        response = self.client.get('/characters?limit=2&skip=1')
        self.assertEqual(response.status_code, 200)
        paginated_data = response.get_json()
        # The response should contain 2 characters
        self.assertEqual(len(paginated_data), 2)

        # Verify that the characters returned are the correct ones
        expected_characters = data[1:3]  # Skip the first character and take the next two
        self.assertEqual(paginated_data, expected_characters)

    def test_get_character_by_id(self):
        """
        Test the GET /characters/<id> endpoint.
        This test checks if the endpoint returns the correct character by ID.
        """
        response = self.client.get('/characters/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # The response should contain the character with ID 1
        self.assertEqual(data['name'], 'Jon Snow')

    def test_get_character_by_invalid_id(self):
        """
        Test the GET /characters/<id> endpoint with an invalid ID.
        This test checks if the endpoint returns a 404 error for a non-existent character.
        """
        response = self.client.get('/characters/invalid_id')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        # The response should contain an error message
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
            # Each character's age should be between 20 and 30
            self.assertTrue(20 <= character['age'] <= 30)

    def test_filter_and_sort_combined(self):
        """
        Test the GET /characters endpoint with combined filtering and sorting.
        This test checks if the endpoint returns correctly filtered and sorted characters.
        """
        response = self.client.get('/characters?house=stark&sort_by=age&order=asc')
        self.assertEqual(response.status_code, 200)
        # The response should contain characters
        data = response.get_json()
        # The characters should be sorted by age in ascending order
        ages = []
        for character in data:
            ages.append(character['age'])
            # Each character should belong to House Stark
        self.assertEqual(ages, sorted(ages))

        # The characters should all belong to House Stark
        for character in data:
            # Each character should belong to House Stark
            self.assertEqual(character['house'].lower(), 'stark')

    def test_add_new_character(self):
        """
        Test the POST /characters endpoint.
        This test checks if a new character can be added to the database.
        """
        new_character = {
            "name": "Antonio Stark",
            "house": "Stark",
            "role": "Software Engineer",
            "age": 55,
            "strength": "Guerrero"
        }
        response = self.client.post('/characters', json=new_character)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        # The response should contain the ID of the new character
        self.assertIn('id', data)

        response = self.client.get(f'/characters/{data["id"]}')
        # The new character should be retrievable by its ID
        self.assertEqual(response.status_code, 200)
        character_data = response.get_json()
        # The retrieved character should match the added character
        self.assertEqual(character_data['name'], new_character['name'])

    def test_edit_character(self):
        """
        Test the PATCH /characters/<id> endpoint.
        This test checks if an existing character can be updated.
        """
        # Ensure the character with ID 3 exists
        response = self.client.get('/characters/3')
        if response.status_code == 404:
            self.skipTest("Character with ID 3 does not exist")

        update_data = {
            "nickname": "The Junior",
            "strength": "Perseverance"
        }
        response = self.client.patch('/characters/3', json=update_data)
        # The endpoint should return a 200 status code
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # The response should contain a success message
        self.assertEqual(data['message'], 'Character updated')

        response = self.client.get('/characters/3')
        # The updated character should have the new data
        self.assertEqual(response.status_code, 200)
        character_data = response.get_json()
        # The character's nickname and strength should be updated
        self.assertEqual(character_data['nickname'], 'The Junior')
        self.assertEqual(character_data['strength'], 'Perseverance')

    def test_edit_nonexistent_character(self):
        """
        Test the PATCH /characters/<id> endpoint with a non-existent character.
        This test checks if the endpoint returns a 404 error for a non-existent character.
        """
        update_data = {
            "nickname": "No One"
        }
        response = self.client.patch('/characters/999', json=update_data)
        # The endpoint should return a 404 error for a non-existent character
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        # The response should contain an error message
        self.assertIn('error', data)

    def test_delete_nonexistent_character(self):
        """
        Test the DELETE /characters/<id> endpoint with a non-existent character.
        This test checks if the endpoint returns a 404 error for a non-existent character.
        """
        response = self.client.delete('/characters/999')
        # The endpoint should return a 404 error for a non-existent character
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        # The response should contain an error message
        self.assertIn('error', data)

    def test_invalid_http_method(self):
        """
        Test an invalid HTTP method on the /characters/<id> endpoint.
        This test checks if the endpoint returns a 405 error for an unsupported HTTP method.
        """
        response = self.client.put('/characters/1', json={})
        # The endpoint should return a 405 error for an unsupported method
        self.assertEqual(response.status_code, 405)

    def test_invalid_filter_attribute(self):
        """
        Test the GET /characters endpoint with an invalid filter attribute.
        This test checks if the endpoint returns a 400 error for an invalid filter attribute.
        """
        response = self.client.get('/characters?height=180')
        # The endpoint should return a 400 error for an invalid
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        # The response should contain an error message
        self.assertIn('error', data)

    def test_delete_last_character(self):
        """
        Test the DELETE /characters/<id> endpoint.
        This test checks if the last character can be deleted.
        """
        # Retrieve the list of characters
        response = self.client.get('/characters')
        # The endpoint should return a 200 status code
        self.assertEqual(response.status_code, 200)
        characters = response.get_json()

        # Get the last character's ID
        last_character_id = characters[-1]['id']

        # Attempt to delete the last character
        response = self.client.delete(f'/characters/{last_character_id}')
        # The endpoint should return a 200 status code
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # The response should contain a success message
        self.assertEqual(data['message'], f"Character '{characters[-1]['name']}' deleted")

        # Verify the character has been deleted
        response = self.client.get(f'/characters/{last_character_id}')
        self.assertEqual(response.status_code, 404)

    def test_filter_characters_by_death_more_than(self):
        """
        Test the GET /characters endpoint with death_more_than filter.
        This test checks if the endpoint returns characters with death year greater than the specified value.
        """
        response = self.client.get('/characters?death_more_than=7')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for character in data:
            self.assertIn('death', character)
            self.assertIsInstance(character['death'], int)
            self.assertTrue(character['death'] > 7)

    def test_filter_characters_by_death_less_than(self):
        """
        Test the GET /characters endpoint with death_less_than filter.
        This test checks if the endpoint returns characters with death year less than the specified value.
        """
        response = self.client.get('/characters?death_less_than=9')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for character in data:
            self.assertIn('death', character)
            self.assertIsInstance(character['death'], int)
            self.assertTrue(character['death'] < 9)

    def test_filter_characters_by_death_range(self):
        """
        Test the GET /characters endpoint with death_more_than and death_less_than filters.
        This test checks if the endpoint returns characters with death year within the specified range.
        """
        response = self.client.get('/characters?death_more_than=4&death_less_than=9')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for character in data:
            self.assertIn('death', character)
            self.assertIsInstance(character['death'], int)
            self.assertTrue(4 < character['death'] < 9)

if __name__ == '__main__':
    unittest.main()