import random
import os
import json

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

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
                        age = int(character_data["age"]) if character_data.get("age") else None
                        death = int(character_data["death"]) if character_data.get("death") else None

                        # We go through the characters in the json file and grab the data
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
        app.db_initialized = True

@app.route("/characters", methods=["GET"])
def get_characters():
    # Getting the query parameters from the request
    # We will use this to filter, sort, and paginate the data
    # Example:
    # /characters?limit=10&skip=0&sort_by=age&order=asc&name=Jon%20Snow&age_more_than=20
    limit = request.args.get("limit", type=int)
    skip = request.args.get("skip", type=int)
    sort_by = request.args.get("sort_by", type=str)
    order = request.args.get("order", "asc", type=str)

    # Create a dictionary of filters from the request arguments
    # To be used in the query.filter() method below
    filters = {}
    for key, value in request.args.items():
        if key not in ["limit", "skip", "sort_by", "order"]:
            filters[key] = value

    valid_filter_fields = ['name', 'house', 'role', 'age', 'strength']

    query = CharacterModel.query  # To be able to filter, sort, and paginate the data

    # Apply filters
    for key, value in filters.items():
        if key == "age_more_than":
            query = query.filter(CharacterModel.age >= int(value))
        elif key == "age_less_than":
            query = query.filter(CharacterModel.age <= int(value))
        elif key in valid_filter_fields:
            query = query.filter(func.lower(getattr(CharacterModel, key)) == value.lower())
        else:
            return jsonify({"error": f"Invalid filter attribute: {key}"}), 400

    # Apply sorting
    if sort_by and sort_by in valid_filter_fields:
        if order == "asc":
            query = query.order_by(getattr(CharacterModel, sort_by).asc())
        else:
            query = query.order_by(getattr(CharacterModel, sort_by).desc())

    # Apply pagination
    if skip is None:
        skip = 0
    if limit is None:
        limit = 20
        characters_query = query.all()
        random.shuffle(characters_query)
        characters_query = characters_query[:limit]
    else:
        characters_query = query.offset(skip).limit(limit).all()

    # Convert the characters to a dictionary so we can jsonify them later
    characters_list = [character.to_dict() for character in characters_query]

    return jsonify(characters_list), 200


# Get a character by ID
@app.route("/characters/<int:id>", methods=["GET"])
def get_character_by_id(id):
    character = CharacterModel.query.get(id)

    if not character:
        return jsonify({"error": "Character not found"}), 404

    return jsonify(character.to_dict()), 200


# Add a new character
@app.route("/characters", methods=["POST"])
def add_character():
    data = request.json
    required_fields = ["name", "role", "age", "strength"]

    # Check if all required fields are entered and valid
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
    return jsonify({"error": "Bad Request"}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(500)
def internal_server_error(error):
    if app.debug:
        return jsonify({"error": str(error)}), 500
    else:
        return jsonify({"error": "Internal Server Error"}), 500


if __name__ == "__main__":
    setup_database()
    app.run(debug=True)