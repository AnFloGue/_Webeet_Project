# app.py
import os
import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
from dotenv import load_dotenv
from urllib.parse import quote
from flask_migrate import Migrate



# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# Database configuration with PostgreSQL using environment variables from .env file
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = quote(os.getenv('POSTGRES_PASSWORD', ''))
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'character_database')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking for better performance

# Initialize the SQLAlchemy object
# bind the database to the app
db = SQLAlchemy(app)

# Initialize the Migrate object binding the app and the database
# to run migrations from the terminal, use the following command:
# flask db init
# flask db migrate -m "Initial migration."
# flask db upgrade

# Not implemented yet
MIgrate = Migrate(app, db)

class CharacterModel(db.Model):
    """
    CharacterModel represents a character in the database.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    house = db.Column(db.String(100), index=True)
    animal = db.Column(db.String(50))
    symbol = db.Column(db.String(50))
    nickname = db.Column(db.String(100))
    role = db.Column(db.String(100), index=True)
    age = db.Column(db.Integer, index=True)
    death = db.Column(db.Integer)
    strength = db.Column(db.String(100))

    def to_dict(self):
        """
        Convert the character model to a dictionary.
        This is necessary because the model is a class, and it cannot be directly used with jsonify.
        By converting it to a dictionary, we can easily jsonify it later.
        """
        return {
            "id": self.id,
            "name": self.name,
            "house": self.house,
            "animal": self.animal,
            "symbol": self.symbol,
            "nickname": self.nickname,
            "role": self.role,
            "age": self.age,
            "death": self.death,
            "strength": self.strength
        }


def initialize_database():
    """
    Initialize the database if it does not exist.
    """
    print("Database does not exist. Creating all tables for the database...")
    db.create_all()

    # Check if there are no characters in the database
    if not CharacterModel.query.first():
        try:
            # Load characters from 'characters.json' file
            with open("characters.json", "r") as file:
                characters_data = json.load(file)

                for character_data in characters_data:
                    # Ensure 'age' is an integer and not empty
                    if character_data.get("age"):
                        age = int(character_data["age"])
                    else:
                        age = None

                    # Ensure 'death' is an integer and not empty
                    if character_data.get("death"):
                        death = int(character_data["death"])
                    else:
                        death = None
                    
                    # Create a new CharacterModel object with each character's data using keyword arguments
                    character_obj = CharacterModel(
                        name=character_data.get("name"),
                        house=character_data.get("house"),
                        animal=character_data.get("animal"),
                        symbol=character_data.get("symbol"),
                        nickname=character_data.get("nickname"),
                        role=character_data.get("role"),
                        age=age,
                        death=death,
                        strength=character_data.get("strength"),
                    )
                    # Add the character to the database session
                    db.session.add(character_obj)
                # Commit the changes
                db.session.commit()
        except FileNotFoundError:
            print("Warning: 'characters.json' file does not exist")
        

# Call the initialize_database function once when the application starts
with app.app_context():
    initialize_database()

@app.before_request
def setup_database():
    """
    Setup the database before dealing with any request.
    """
    if not hasattr(app, 'db_initialized'):
        app.db_initialized = True

@app.route("/", methods=["GET"])
def home():
    """
    Home route that returns a welcome message.
    """
    return jsonify({"message": "Welcome to the Character API"}), 200

# @app.route("/print_characters", methods=["GET"])
# def print_characters():
#     """
#     Print the content of the characters table for debuging purposes.
#     """
#     # Execute the query to retrieve all characters
#     all_characters = CharacterModel.query.all()
#
#     # Convert the query results to a list of dictionaries
#     characters_list = []
#     for character in all_characters:
#         characters_list.append(character.to_dict())
#
#     # Print the list of characters to the console
#     for character in characters_list:
#
#         print(character)
#
#     # Return the list of characters as a JSON response
#     return jsonify(characters_list), 200

@app.route("/characters", methods=["GET"])
def get_characters():
    """
    Fetch and filter characters from the CharacterModel table.
    
    Filters are applied based on query parameters passed in the request.
    Supported filters:
    
        - Numeric filters:
            * age_more_than: Filters for characters with age greater than or equal to the given value.
            * age_less_than: Filters for characters with age less than or equal to the given value.
            * age: Filters for characters with age equal to the given value.
            * death_more_than: Filters for characters with death greater than or equal to the given value.
            
        - String filters:
            * name: Filters for characters whose names contain the given value (case-insensitive).
            * house: Filters for characters whose house contains the given value (case-insensitive).
            * role: Filters for characters whose role contains the given value (case-insensitive).
            * strength: Filters for characters whose strength contains the given value (case-insensitive).
    
    Additional features:
    
            once we have the filters, we can sort the results by a specific field and order.
    
        - Sorting:
            * Supported fields: id, name, house, role, age, strength.
            * Use the 'sort_by' parameter to specify the field and 'order' for ascending or descending order.
            * Defaults to sorting by 'id' in ascending order if no valid sort_by is provided.
            
        - Pagination:
            * Use 'limit' to specify the maximum number of results to return.
            * Use 'skip' to specify the number of results to skip.
            * If no pagination is provided, defaults to a random selection of 20 characters.
    
    Returns:
        - A JSON response with the filtered and paginated characters or an error message for invalid filters or values.
    """
    # ========================================================
    # Filtering preparation
    # ========================================================
    
    # Retrieve pagination and sorting parameters from the request
    limit = request.args.get("limit")
    skip = request.args.get("skip")
    sort_by = request.args.get("sort_by", type=str)
    order = request.args.get("order", "asc", type=str)
    
    # Convert limit and skip to integers, handling invalid values
    try:
        limit = int(limit) if limit is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid value for limit: must be an integer"}), 400
    
    try:
        skip = int(skip) if skip is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid value for skip: must be an integer"}), 400

    # Initialize a dictionary to store filter parameters from the request.
    # we store filters that are not pagination or sorting parameters
    filters = {}
    for key, value in request.args.items():
        if key not in ["limit", "skip", "sort_by", "order"]:
            filters[key] = value

    # Initialize the query object. A query for all records in the CharacterModel table
    query = CharacterModel.query

    # ========================================================
    # Filtering execution
    # ========================================================
    
    # Apply filters to the query by checking which filters are present in the request
    # norrowing down the results by applying cumulatively the filters I use "and" operator (default in SQLAlchemy) and not "or" in the query
    
    for key, value in filters.items():
        # Handle numeric filters (requires validation)
        if key in ["age_more_than", "age_less_than", "age", "death_more_than", "death_less_than", "death"]:
            try:
                value = int(value)
                if key == "age_more_than":
                    query = query.filter(CharacterModel.age >= value)
                elif key == "age_less_than":
                    query = query.filter(CharacterModel.age <= value)
                elif key == "age":
                    query = query.filter(CharacterModel.age == value)
                elif key == "death_more_than":
                    query = query.filter(CharacterModel.death > value)
                elif key == "death_less_than":
                    query = query.filter(CharacterModel.death < value)
                elif key == "death":
                    query = query.filter(CharacterModel.death == value)
            except ValueError:
                return jsonify({"error": f"Invalid value for {key}: must be an integer"}), 400
        
        # Handle string filters
        elif key in ["name", "house", "role", "strength"]:
            if key == "name":
                query = query.filter(CharacterModel.name.ilike(f"%{value}%"))
            elif key == "house":
                query = query.filter(CharacterModel.house.ilike(f"%{value}%"))
            elif key == "role":
                query = query.filter(CharacterModel.role.ilike(f"%{value}%"))
            elif key == "strength":
                query = query.filter(CharacterModel.strength.ilike(f"%{value}%"))
        else:
            return jsonify({"error": f"Invalid filter attribute: {key}"}), 400
        
    # ========================================================
    # Sorting
    # ========================================================
    # List of valid sort fields
    valid_sort_fields = ['id', 'name', 'house', 'role', 'age', 'strength', 'animal', 'symbol', 'nickname', 'death']

    # Apply sorting to the query. Sorting happens only after all filters have been applied.
    if sort_by in valid_sort_fields:
        if order == "asc":
            # gets the column name based on the value of sort_by and sorts the query in ascending order
            query = query.order_by(getattr(CharacterModel, sort_by).asc())
        else:
            query = query.order_by(getattr(CharacterModel, sort_by).desc())
    else:
        # If the sort_by parameter is invalid, we sort by ID in ascending order by default
        query = query.order_by(CharacterModel.id.asc())

    # ========================================================
    # Pagination
    # ========================================================
    
    # 	If neither limit nor skip is provided, we take a random subset of 20 characters from the filtered results
    if limit is None and skip is None:
        characters_query = query.order_by(func.random()).limit(20).all()
    
    # If limit is provided but skip is not, we return the first 'limit' results from the filtered query but if limit
    # is provided and skip is not, we return the first 'limit' results from the filtered query
    else:
        # If skip is not provided, we set it to 0 to start from the beginning
        if skip is None:
            skip = 0
        # If limit is not provided, we set it to None to return all results
        if limit is None:
            characters_query = query.offset(skip).all()
        else:
            characters_query = query.offset(skip).limit(limit).all()

    # ========================================================
    # Response
    # ========================================================
    
    # Convert the query results to a list of dictionaries
    characters_list = []
    for character in characters_query:
        characters_list.append(character.to_dict())

    # Return the list of characters as a JSON response
    return jsonify(characters_list), 200

@app.route("/characters/<int:id>", methods=["GET"])
def get_character_by_id(id):
    """
    Get a character by its ID.
    """
    character = CharacterModel.query.get(id)

    if not character:
        return jsonify({"error": "Character not found"}), 404

    return jsonify(character.to_dict()), 200

@app.route("/characters", methods=["POST"])
def add_character():
    """
    Add a new character to the database.
    """
    # Retrieve the JSON payload from the request and convert it to a dictionary
    data_request = request.json
    
    # define the minimum fields that must be present in the request
    # payload for the character to be added to the database
    required_fields = ["name", "role", "age", "strength"]

    for field in required_fields:
        # Check if the required field is missing or empty
        if field not in data_request or not data_request[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Check if 'age' is an integer
    if not isinstance(data_request["age"], int):
        return jsonify({"error": "'age' must be an integer"}), 400
    # Check if 'name' is a string
    if not isinstance(data_request["name"], str):
        return jsonify({"error": "'name' must be a string"}), 400
    # Check if 'role' is a string
    if not isinstance(data_request["role"], str):
        return jsonify({"error": "'role' must be a string"}), 400
    # Check if 'strength' is a string
    if not isinstance(data_request["strength"], str):
        return jsonify({"error": "'strength' must be a string"}), 400

    # Create a new CharacterModel object with the data from the request
    new_character = CharacterModel(
        name=data_request["name"],
        house=data_request.get("house"),
        animal=data_request.get("animal"),
        symbol=data_request.get("symbol"),
        nickname=data_request.get("nickname"),
        role=data_request["role"],
        age=data_request["age"],
        death=data_request.get("death"),
        strength=data_request["strength"]
    )
    # Add the new character to the database
    db.session.add(new_character)
    db.session.commit()
    # Returned the new character's data as a JSON response with information about the added character
    return jsonify({"message": "Character added", "name": new_character.name, "id": new_character.id}), 201

@app.route("/characters/<int:id>", methods=["PATCH"])
def edit_character(id):
    """
    Edit an existing character by its ID.
    """
    character = CharacterModel.query.get(id)
    # Check if the character exists
    if not character:
        return jsonify({"error": "Character not found"}), 404

    # Get the JSON payload data from the request
    request_payload = request.json
    
    editable_fields = ['name', 'house', 'animal', 'symbol', 'nickname', 'role', 'age', 'death', 'strength']

    # go through each element in the editable_fields list
    for field in editable_fields:
        # and check if the field is in the request_payload
        if field in request_payload:
            # if the field is in the request_payload, we set the value of the field in the
            # character object to the value in the request_payload that we get from the request_payload dictionary
            setattr(character, field, request_payload[field])

    db.session.commit()
    return jsonify({"message": "Character updated"}), 200

@app.route("/characters/<int:id>", methods=["DELETE"])
def delete_character(id):
    """
    Delete a character by its ID.
    """
    character = CharacterModel.query.get(id)
    # Check if the character exists
    if not character:
        return jsonify({"error": "Character not found"}), 404

    db.session.delete(character)
    db.session.commit()
    return jsonify({"message": f"Character '{character.name}' deleted"}), 200

# Error Handling
@app.errorhandler(400)
def bad_request(error):
    """
    Handle 400 Bad Request errors.
    """
    return jsonify({"error": "Bad Request"}), 400

@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 Not Found errors.
    """
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def internal_server_error(error):
    """
    Handle 500 Internal Server Error errors.
    """
    if app.debug:
        return jsonify({"error": str(error)}), 500
    else:
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run(debug=True)