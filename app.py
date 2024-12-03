import random
import os
import json

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc

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
    id = db.Column(db.Integer, primary_key=True)
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
    print("Setting up the database...")
    db.create_all()  # Creates all tables if they do not already exist
    if not CharacterModel.query.first():  # Populate the database only if it's empty
        try:
            with open("characters.json", "r") as file:
                characters_data = json.load(file)

                for character_data in characters_data:
                    # Convert age and death to integers if they exist, else set to None
                    age = int(character_data["age"]) if character_data.get("age") else None
                    death = int(character_data["death"]) if character_data.get("death") else None

                    character_obj = CharacterModel(
                        id=character_data["id"],
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
            print("Attention!!! - characters.json - does not exist")

@app.route("/characters", methods=["GET"])
def get_characters():
    limit = request.args.get("limit", type=int)
    skip = request.args.get("skip", type=int)
    sort_by = request.args.get("sort_by", type=str)
    order = request.args.get("order", "asc", type=str)
    filters = {key: value for key, value in request.args.items() if key not in ["limit", "skip", "sort_by", "order"]}

    valid_fields = ['id', 'name', 'house', 'animal', 'symbol', 'nickname', 'role', 'age', 'death', 'strength']
    valid_sort_fields = valid_fields

    if sort_by and sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field: {sort_by}"}), 400

    query = CharacterModel.query

    # Apply filters
    for attr, value in filters.items():
        if attr == "age_more_than":
            query = query.filter(CharacterModel.age >= int(value))
        elif attr == "age_less_than":
            query = query.filter(CharacterModel.age <= int(value))
        elif attr in valid_fields:
            query = query.filter(getattr(CharacterModel, attr).ilike(f"%{value}%"))
        else:
            return jsonify({"error": f"Invalid filter attribute: {attr}"}), 400

    # Apply sorting
    if sort_by:
        if sort_by == "age":
            query = query.filter(CharacterModel.age != None)
        if order == "asc":
            query = query.order_by(asc(getattr(CharacterModel, sort_by)))
        else:
            query = query.order_by(desc(getattr(CharacterModel, sort_by)))

    # Apply pagination
    if limit is None and skip is None:
        characters = query.all()
        random_characters = random.sample(characters, min(20, len(characters)))
        characters_list = [character.to_dict() for character in random_characters]
    else:
        if skip is None:
            skip = 0
        if limit is None:
            limit = 20
        characters_query = query.offset(skip).limit(limit).all()
        characters_list = [character.to_dict() for character in characters_query]

    return jsonify(characters_list), 200

# Get a character by ID
@app.route("/characters/<int:id>", methods=["GET"])
def get_character_by_id(id):
    character = CharacterModel.query.get(id)

    if not character:
        return jsonify({"error": "Attention!!! - Character does not exist"}), 404

    return jsonify(character.to_dict()), 200

# Add a new character
@app.route("/characters", methods=["POST"])
def add_character():
    data = request.json
    required_fields = ["id", "name", "role", "age", "strength"]

    # Check if all required fields are inputted and valid
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Attention!!! - Missing required field: {field}"}), 400

    # Validate data types
    if not isinstance(data["id"], int):
        return jsonify({"error": "Attention!!! - 'id' must be an integer"}), 400
    if not isinstance(data["age"], int):
        return jsonify({"error": "Attention!!! - 'age' must be an integer"}), 400
    if not isinstance(data["name"], str):
        return jsonify({"error": "Attention!!! - 'name' must be a string"}), 400
    # Additional validation can be added here

    # Check if the character with the same id already exists
    existing_character = CharacterModel.query.get(data["id"])
    if existing_character:
        return jsonify({"error": "Attention!!! - Character with this ID already exists"}), 400

    # Create a new CharacterModel instance
    new_character = CharacterModel(
        id=data["id"],
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

    return jsonify({"message": "Character added"}), 201

# Edit a character by ID
@app.route("/characters/<int:id>", methods=["PATCH"])
def edit_character(id):
    character = CharacterModel.query.get(id)

    if not character:
        return jsonify({"error": "Attention!!! - Character not found"}), 404

    data = request.json

    # Update fields if present in the request
    for field in ['name', 'house', 'animal', 'symbol', 'nickname', 'role', 'age', 'death', 'strength']:
        if field in data:
            setattr(character, field, data[field])

    db.session.commit()
    return jsonify({"message": "Character updated"}), 200

# Delete a character by ID
@app.route("/characters/<int:id>", methods=["DELETE"])
def delete_character(id):
    character = CharacterModel.query.get(id)

    if not character:
        return jsonify({"error": "Attention!!! - Character not found"}), 404

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
    return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run(debug=True)