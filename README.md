# Webeet Project

A Flask-based REST API for managing character data with PostgreSQL backend.

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [API Documentation](#api-documentation)
  - [Character Endpoints](#character-endpoints)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Testing URLs](#testing-urls)
  - [GET Requests](#get-requests)
    - [Basic Queries](#basic-queries)
    - [Filtering](#filtering)
    - [Age-Based Filtering](#age-based-filtering)
    - [Sorting](#sorting)
    - [Combined Queries](#combined-queries)
  - [POST Request Examples](#post-request-examples)
  - [Error Testing](#error-testing)

## Features

- Full CRUD operations for character management
- Advanced filtering and sorting capabilities
- Pagination support
- Error handling and validation
- PostgreSQL database integration

## Tech Stack

- **Backend**: Python 3.7+, Flask
- **Database**: PostgreSQL
- **Testing**: Unittest
- **Dependencies**: SQLAlchemy, python-dotenv

## Getting Started

### Prerequisites

- Python 3.7 or higher
- PostgreSQL
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone [repository URL]
   ```

2. Navigate to the project directory:
   ```bash
   cd webeet-project
   ```

3. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure environment variables:
   - Create a `.env` file in the project root
   - Add the following variables:
     ```
     POSTGRES_USER=your_username
     POSTGRES_PASSWORD=your_password
     DB_NAME=character_database
     DB_HOST=localhost
     DB_PORT=5432
     ```

6. Run the application:
   ```bash
   flask run
   ```

## API Documentation

### Character Endpoints

#### Get All Characters
```http
GET /characters
```

Query Parameters:
- `limit` (int): Maximum number of records to return
- `skip` (int): Number of records to skip
- `sort_by` (string): Field to sort by (name, house, role, age, strength)
- `order` (string): Sort order (asc, desc)
- `name` (string): Filter by name
- `house` (string): Filter by house
- `role` (string): Filter by role
- `age` (int): Filter by exact age
- `age_more_than` (int): Filter by minimum age
- `age_less_than` (int): Filter by maximum age
- `death` (int): Filter by exact death year
- `death_more_than` (int): Filter by minimum death year
- `death_less_than` (int): Filter by maximum death year
- `strength` (string): Filter by strength level

#### Get Character by ID
```http
GET /characters/{id}
```

#### Create Character
```http
POST /characters
```

Request Body:
```json
{
  "name": "Character Name",
  "house": "House Name",
  "animal": "House Animal",
  "symbol": "House Symbol",
  "nickname": "Character Nickname",
  "role": "Character Role",
  "age": 25,
  "death": null,
  "strength": "High"
}
```

#### Update Character
```http
PUT /characters/{id}
```

Request Body: Same as POST, with fields to update

#### Delete Character
```http
DELETE /characters/{id}
```

## Error Handling

The API includes proper error handling for:
- 400 Bad Request
- 404 Not Found
- 500 Internal Server Error

## Testing

Run the test suite:
```bash
python -m unittest test_webeet.py
```

## Testing URLs

Here's a comprehensive list of URLs for testing the API endpoints:

### GET Requests

#### Basic Queries
- [Get all characters](http://127.0.0.1:5000/characters)
- [Get characters with pagination](http://127.0.0.1:5000/characters?limit=10&skip=0)
- [Get character by ID](http://127.0.0.1:5000/characters/1)

#### Filtering
- [Filter by name](http://127.0.0.1:5000/characters?name=Shae)
- [Filter by house](http://127.0.0.1:5000/characters?house=Lannister)
- [Filter by role](http://127.0.0.1:5000/characters?role=Handmaiden)
- [Filter by name and house](http://127.0.0.1:5000/characters?name=Hodor&house=Stark)

#### Age-Based Filtering
- [Age greater than...](http://127.0.0.1:5000/characters?age_more_than=25)
- [Age less than...](http://127.0.0.1:5000/characters?age_less_than=30)
- [Age range](http://127.0.0.1:5000/characters?age_more_than=20&age_less_than=22)

#### Death-Based Filtering
- [Death year greater than...](http://127.0.0.1:5000/characters?death_more_than=9)
- [Death year less than...](http://127.0.0.1:5000/characters?death_less_than=7)
- [Death year range](http://127.0.0.1:5000/characters?death_more_than=6&death_less_than=8)
- [Death year equal to...](http://127.0.0.1:5000/characters?death=1)

#### Sorting
- [Sort by age (ascending)](http://127.0.0.1:5000/characters?sort_by=age&order=asc)
- [Sort by name (descending)](http://127.0.0.1:5000/characters?sort_by=name&order=desc)
- [Sort by house (ascending)](http://127.0.0.1:5000/characters?sort_by=house&order=asc)

#### Combined Queries
- [Filter and sort by house and age](http://127.0.0.1:5000/characters?house=Stark&sort_by=age&order=asc)
- [Filter and sort by role, age, and name](http://127.0.0.1:5000/characters?role=Knight&age_more_than=30&sort_by=name&order=asc)
- [Complex query 1](http://127.0.0.1:5000/characters?limit=10&skip=0&sort_by=age&order=asc&name=Jon%20Snow&age_more_than=20)
- [Complex query 2](http://127.0.0.1:5000/characters?limit=5&skip=1&sort_by=age&order=asc&house=Stark)
- [Filter by strength and house with pagination](http://127.0.0.1:5000/characters?strength=Intelligence&house=Stark&limit=5&skip=0)

#### Print Characters in the Browser and in the Console
- [Filter and sort by house and age](http://127.0.0.1:5000//print_characters)

### POST Request Examples

To create a new character, send a POST request to `http://127.0.0.1:5000/characters` with the following JSON body:

```json
{
  "name": "Test Character",
  "house": "Test House",
  "animal": "Test Animal",
  "symbol": "Test Symbol",
  "nickname": "Tester",
  "role": "Tester Role",
  "age": 30,
  "death": null,
  "strength": "Testing"
}
```

### Error Testing
- [Get non-existent character](http://127.0.0.1:5000/characters/9999)

> **Note**: All URLs are clickable and assume the API is running locally on port 5000. Make sure the server is running before testing.