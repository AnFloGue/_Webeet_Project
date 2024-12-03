import random

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import os

app = Flask(__name__)

# absolute path of the directory containing this script
basedir = os.path.abspath(os.path.dirname(__file__))

# Database configuration with absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'characters.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Better performance

db = SQLAlchemy(app)

# Ensure the database directory exists
database_dir = os.path.join(basedir, 'database')
if not os.path.exists(database_dir):
    os.makedirs(database_dir)


# modelling the Character table for the database
class CharacterModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    house = db.Column(db.String(100))
    animal = db.Column(db.String(50))
    symbol = db.Column(db.String(50))
    nickname = db.Column(db.String(100))
    role = db.Column(db.String(100))
    age = db.Column(db.Integer)
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
    db.create_all()  # creates all tables if they do not already exist
    if not CharacterModel.query.first():  # checking by looking for first entry, and only populate the database if it is empty
        try:
            with open("characters.json", "r") as file:
                characters_data = json.load(file)

                for character_obj in characters_data:
                    # we go through the characters in the json file and grab the data
                    # then instantiating an object of the CharacterModel class for each character

                    character_obj = CharacterModel(
                        id=character_obj["id"],
                        name=character_obj["name"],
                        house=character_obj.get("house"),
                        animal=character_obj.get("animal"),
                        symbol=character_obj.get("symbol"),
                        nickname=character_obj.get("nickname"),
                        role=character_obj["role"],
                        age=character_obj["age"],
                        death=character_obj.get("death"),
                        strength=character_obj["strength"]
                    )
                    # we add the character object to the database session
                    db.session.add(character_obj)

                db.session.commit()

        except FileNotFoundError:
            print("Attention!!! - characters.json - does not exist")


# Get all characters and paginate them
@app.route("/characters", methods=["GET"])
def get_characters():
    limit = request.args.get("limit", type=int)
    skip = request.args.get("skip", type=int)
    sort_by = request.args.get("sort_by", type=str)
    order = request.args.get("order", "asc", type=str)
    filters = {key: value for key, value in request.args.items() if key not in ["limit", "skip", "sort_by", "order"]}

    query = CharacterModel.query

    for attr, value in filters.items():
        if attr == "age_more_than":
            query = query.filter(CharacterModel.age >= int(value))
        elif attr == "age_less_than":
            query = query.filter(CharacterModel.age <= int(value))
        else:
            query = query.filter(getattr(CharacterModel, attr).ilike(f"%{value}%"))

    if sort_by:
        if order == "asc":
            query = query.order_by(getattr(CharacterModel, sort_by).asc())
        else:
            query = query.order_by(getattr(CharacterModel, sort_by).desc())

    if limit is None and skip is None:
        characters = query.all()
        random_characters = random.sample(characters, min(20, len(characters)))
        characters_paginated_list = [character.to_dict() for character in random_characters]
    else:
        characters_paginated_query = query.offset(skip).limit(limit).all()
        characters_paginated_list = [character.to_dict() for character in characters_paginated_query]

    return jsonify(characters_paginated_list), 200


# Get a character by ID
@app.route("/characters/<int:id>", methods=["GET"])
def get_character_by_id(id):
    character_by_id = CharacterModel.query.get(id)

    if not character_by_id:
        return jsonify({"error": "Attention!!! - Character does not exist"}), 404

    # if character exist, we create a dictionary with the character data
    character_data = {
        "id": character_by_id.id,
        "name": character_by_id.name,
        "house": character_by_id.house,
        "animal": character_by_id.animal,
        "symbol": character_by_id.symbol,
        "nickname": character_by_id.nickname,
        "role": character_by_id.role,
        "age": character_by_id.age,
        "death": character_by_id.death,
        "strength": character_by_id.strength
    }

    return jsonify(character_data), 200

# Add a new character
@app.route("/characters", methods=["POST"])
def add_character():
    data = request.json
    required_fields = ["id", "name", "house", "animal", "symbol", "nickname", "role", "age", "death", "strength"]

    # Check if all required fields are inputted and valid
    for field in required_fields:
        if field not in data or not isinstance(data[field], (str, int)):
            return jsonify({"error": f"Attention!!! - Missing or invalid required field: {field}"}), 400

    # Clear the session to avoid stale data
    db.session.expire_all()

    # Check if the character with the same id already exists
    existing_character = CharacterModel.query.get(data["id"])
    if existing_character:
        return jsonify({"error": "Attention!!! - Character with this ID already exists"}), 400

    # Create a new CharacterModel database using the dictionary
    new_character = CharacterModel(
        id=data["id"],
        name=data["name"],
        house=data["house"],
        animal=data["animal"],
        symbol=data["symbol"],
        nickname=data["nickname"],
        role=data["role"],
        age=data["age"],
        death=data["death"],
        strength=data["strength"]
    )

    db.session.add(new_character)
    db.session.commit()

    return jsonify({"message": "Character added"}), 201
# Edit a character by ID
@app.route("/characters/<int:id>", methods=["PATCH"])
def edit_character(id):
    
    # we get an instance of the CharacterModel class with the id
    characters_id = CharacterModel.query.get(id)
    
    # check if the character exists
    if not characters_id:
        return jsonify({"error": "Attention!!! - Character not found"}), 404

    # if the field is in the request, we update the field that is in the request by using
    # the CharacterModel object method
    characters_updates = request.json
    if "name" in characters_updates:
        characters_id.name = characters_updates["name"]
    if "house" in characters_updates:
        characters_id.house = characters_updates["house"]
    if "animal" in characters_updates:
        characters_id.animal = characters_updates["animal"]
    if "symbol" in characters_updates:
        characters_id.symbol = characters_updates["symbol"]
    if "nickname" in characters_updates:
        characters_id.nickname = characters_updates["nickname"]
    if "role" in characters_updates:
        characters_id.role = characters_updates["role"]
    if "age" in characters_updates:
        characters_id.age = characters_updates["age"]
    if "death" in characters_updates:
        characters_id.death = characters_updates["death"]
    if "strength" in characters_updates:
        characters_id.strength = characters_updates["strength"]

    db.session.commit()
    return jsonify({"message": "Character updated"}), 200


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