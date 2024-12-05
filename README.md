# Webeet Project

## Overview

The Webeet Project is a Flask-based web application that manages characters from a fictional universe. It provides a RESTful API to perform CRUD operations on character data stored in a SQLite database.

## Features

- Retrieve all characters
- Retrieve characters with pagination
- Filter characters by various attributes (name, house, role, age, etc.)
- Sort characters by different attributes
- Add new characters
- Edit existing characters
- Delete characters

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/AnFloGue/Webeet_Project.git
    cd Webeet_Project
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```sh
    python setup_database.py
    ```

## Running the Application

1. Start the Flask application:
    ```sh
    flask run
    ```

2. Open your browser and navigate to `http://127.0.0.1:5000`.

## API Endpoints

### GET Requests

- **Retrieve all characters**: `GET /characters`
- **Retrieve characters with pagination**: `GET /characters?limit=10&skip=0`
- **Filter characters by name**: `GET /characters?name=Shae`
- **Filter characters by house**: `GET /characters?house=Lannister`
- **Filter characters by role**: `GET /characters?role=Handmaiden`
- **Filter characters by age range**: `GET /characters?age_more_than=20&age_less_than=30`
- **Sort characters by age in ascending order**: `GET /characters?sort_by=age&order=asc`
- **Retrieve a character by ID**: `GET /characters/<id>`

### POST Requests

- **Add a new character**: `POST /characters`
    - Example JSON body:
      ```json
      {
        "name": "Test Character",
        "house": "Test House",
        "role": "Tester",
        "age": 30,
        "strength": "Testing"
      }
      ```

### PATCH Requests

- **Edit an existing character**: `PATCH /characters/<id>`
    - Example JSON body:
      ```json
      {
        "nickname": "The Imp",
        "strength": "Wit"
      }
      ```

### DELETE Requests

- **Delete a character**: `DELETE /characters/<id>`

## Running Tests

To run the unit tests, use the following command:
```sh
python -m unittest discover