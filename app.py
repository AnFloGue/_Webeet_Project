# app.py
import random
import os
import json

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Absolute path of the directory containing this script
basedir = os.path.abspath(os.path.dirname(__file__))

# Database configuration with absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'characters.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Better performance

db = SQLAlchemy(app)

# Ensure the database directory exists
database_dir = os.path.join(basedir, 'database')
if not os.path.exists(database_dir):
    os.makedirs(database_dir)


# Modeling the Character table for the database
class CharacterModel(db.Model):
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
    
    # Converting the CharacterModel object to a dictionary because jsonify() only accepts dictionaries and lists
    def to_dict(self):
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


@app.before_request
def setup_database():
    if not hasattr(app, 'db_initialized'):
        print("Creating all tables for the database...")
        db.create_all()  # Creates all tables if they do not already exist
        if not CharacterModel.query.first():  # Only populate the database if it is empty
            try:
                with open("characters.json", "r") as file:
                    characters_data = json.load(file)
                    
                    for character_data in characters_data:
                        # Convert age and death to integers if they exist, else set to None
                        if character_data.get("age"):
                            age = int(character_data["age"])
                        else:
                            age = None
                        
                        if character_data.get("death"):
                            death = int(character_data["death"])
                        else:
                            death = None
                        
                        # Instantiating an object of the CharacterModel class for each character
                        character_obj = CharacterModel(
                            name=character_data["name"],
                            house=character_data.get("house"),
                            animal=character_data.get("animal"),
                            symbol=character_data.get("symbol"),
                            nickname=character_data.get("nickname"),
                            role=character_data["role"],
                            age=age,
                            death=death,
                            strength=character_data["strength"]
                        )
                        db.session.add(character_obj)
                    
                    db.session.commit()
            
            except FileNotFoundError:
                print("Warning: 'characters.json' does not exist")
        
        # We avoid reinitializing the database so that the data is not being duplicated
        app.db_initialized = True


@app.route("/characters", methods=["GET"])
def get_characters():
    """
    Fetch all characters with optional pagination, filtering, and sorting.

    Query Parameters:
        - limit (int): Number of results per page.
        - skip (int): Number of results to skip.
        - sort_asc (str): Field to sort in ascending order.
        - sort_des (str): Field to sort in descending order.
        - Filters for character attributes (name, house, role, age, strength).
        - age_more_than (int): Filter for age greater than or equal to a value.
        - age_less_than (int): Filter for age less than or equal to a value.
    """
    limit = request.args.get("limit", type=int)
    skip = request.args.get("skip", type=int)
    sort_asc = request.args.get("sort_asc", type=str)
    sort_des = request.args.get("sort_des", type=str)
    
    filters = {}
    # Get all parameters in the request that are not limit, skip, sort_asc, or sort_des and
    # add them to the filters dictionary so that we can filter the query. With this,
    # we can apply these filters to the database query and get the requested data.
    for key, value in request.args.items():
        if key not in ["limit", "skip", "sort_asc", "sort_des"]:
            filters[key] = value
    
    valid_filter_fields = ['age', 'name', 'house', 'role', 'strength']
    
    query = CharacterModel.query
    
    for key, value in filters.items():
        if key == "age_more_than":  # Query parameter that should come from the request URL
            try:
                query = query.filter(CharacterModel.age >= int(value))
            except ValueError:
                return jsonify({"error": f"Invalid value for {key}: must be an integer"}), 400
        elif key == "age_less_than":
            try:
                query = query.filter(CharacterModel.age <= int(value))
            except ValueError:
                return jsonify({"error": f"Invalid value for {key}: must be an integer"}), 400
        elif key in valid_filter_fields:
            if key == "age":
                try:
                    query = query.filter(CharacterModel.age == int(value))
                except ValueError:
                    return jsonify({"error": f"Invalid value for {key}: must be an integer"}), 400
            else:
                # Case-insensitive filtering
                query = query.filter(getattr(CharacterModel, key).ilike(f"%{value}%"))
        else:
            return jsonify({"error": f"Invalid filter attribute: {key}"}), 400
    
    # Sorting
    valid_sort_fields = ['name', 'house', 'role', 'age', 'strength']
    if sort_asc and sort_asc in valid_sort_fields:
        query = query.order_by(getattr(CharacterModel, sort_asc).asc())
    elif sort_des and sort_des in valid_sort_fields:
        query = query.order_by(getattr(CharacterModel, sort_des).desc())
    elif sort_asc or sort_des:
        # Invalid sort field provided
        invalid_field = sort_asc if sort_asc else sort_des
        return jsonify({"error": f"Invalid sort field: {invalid_field}"}), 400
    
    # Check for skip value exceeding available data
    total_records = query.count()
    if skip is not None and skip >= total_records:
        return jsonify({"error": "Skip value exceeds the number of available characters"}), 400
    
    # If limit is not provided, return 20 random characters
    if limit is None and skip is None:
        limit = 20
        characters_query = query.all()
        if not characters_query:
            return jsonify({"error": "No characters found"}), 404
        random.shuffle(characters_query)
        characters_query = characters_query[:limit]
    else:
        if skip is None:
            skip = 0
        if limit is None:
            characters_query = query.offset(skip).all()
        else:
            characters_query = query.offset(skip).limit(limit).all()
    
    characters_list = [character.to_dict() for character in characters_query]
    
    return jsonify(characters_list), 200


# Get a character by ID
@app.route("/characters/<int:id>", methods=["GET"])
def get_character_by_id(id):
    """
    Fetch a specific character by their ID.
    """
    character = CharacterModel.query.get(id)
    
    if not character:
        return jsonify({"error": "Character not found"}), 404
    
    return jsonify(character.to_dict()), 200


# Add a new character
@app.route("/characters", methods=["POST"])
def add_character():
    """
    Add a new character to the database.

    Expected JSON Payload:
        - name (str): Name of the character.
        - role (str): Role of the character.
        - age (int): Age of the character.
        - strength (str): Strength of the character.
        - Optional fields: house, animal, symbol, nickname, death.
    """
    data = request.json
    required_fields = ["name", "role", "age", "strength"]
    
    # Check if all minimum required fields are entered and valid
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Checking that data is the right type
    if not isinstance(data["age"], int):
        return jsonify({"error": "'age' must be an integer"}), 400
    if not isinstance(data["name"], str):
        return jsonify({"error": "'name' must be a string"}), 400
    
    # Create a new CharacterModel instance with the data from the request
    new_character = CharacterModel(
        name=data["name"],
        house=data.get("house"),
        animal=data.get("animal"),
        symbol=data.get("symbol"),
        nickname=data.get("nickname"),
        role=data["role"],
        age=data["age"],
        death=data.get("death"),
        strength=data["strength"]
    )
    
    db.session.add(new_character)
    db.session.commit()
    
    return jsonify({"message": "Character added", "id": new_character.id}), 201


# Edit a character by ID
@app.route("/characters/<int:id>", methods=["PATCH"])
def edit_character(id):
    """
    Edit an existing character by their ID.

    Expected JSON Payload:
        - Any of the character fields to update.
    """
    # Get the character by ID
    character = CharacterModel.query.get(id)
    
    # Check if the character exists
    if not character:
        return jsonify({"error": "Character not found"}), 404
    
    data = request.json
    
    fields = ['name', 'house', 'animal', 'symbol', 'nickname', 'role', 'age', 'death', 'strength']
    
    # Update fields if present in the request
    for field in fields:
        if field in data:
            setattr(character, field, data[field])
    
    db.session.commit()
    return jsonify({"message": "Character updated"}), 200


# Delete a character by ID
@app.route("/characters/<int:id>", methods=["DELETE"])
def delete_character(id):
    """
    Delete a character by their ID.
    """
    # Get the character by ID
    character = CharacterModel.query.get(id)
    
    # Check if the character exists
    if not character:
        return jsonify({"error": "Character not found"}), 404
    
    db.session.delete(character)
    db.session.commit()
    return jsonify({"message": "Character deleted"}), 200


# Error handlers
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


@app.errorhandler(405)
def method_not_allowed(error):
    """
    Handle 405 Method Not Allowed errors.
    """
    return jsonify({"error": "Method Not Allowed"}), 405


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
    setup_database()
    app.run(debug=True)