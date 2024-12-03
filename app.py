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
    # pagination
    limit = request.args.get("limit", 1, type=int)
    skip = request.args.get("skip", 4, type=int)
    characters_paginated_query = CharacterModel.query.offset(skip).limit(limit).all()
    
    characters_paginated_list = []
    
    for characters in characters_paginated_query:
        character_dict = {
            "id": characters.id,
            "name": characters.name,
            "house": characters.house,
            "animal": characters.animal,
            "symbol": characters.symbol,
            "nickname": characters.nickname,
            "role": characters.role,
            "age": characters.age,
            "death": characters.death,
            "strength": characters.strength
        }
        characters_paginated_list.append(character_dict)
    
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


@app.route("/characters", methods=["POST"])
def add_character():
    data = request.json
    required_fields = ["id", "name", "house", "animal", "symbol", "nickname", "role", "age", "death", "strength"]
    
    # Check if all required fields are inputted
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Clear the session to avoid stale data
    db.session.expire_all()
    
    # Check if the character with the same id already exists
    existing_character = CharacterModel.query.get(data["id"])
    if existing_character:
        return jsonify({"error": "Character with this ID already exists"}), 400
    
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


if __name__ == "__main__":
    app.run(debug=True)