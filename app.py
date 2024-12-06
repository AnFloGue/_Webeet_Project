import os
import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from urllib.parse import quote

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Database configuration with PostgreSQL using environment variables
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = quote(os.getenv('POSTGRES_PASSWORD', ''))
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'character_database')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Better performance

db = SQLAlchemy(app)

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

@app.before_request
def setup_database():
    """
    Setup the database before handling any request.
    """
    if not hasattr(app, 'db_initialized'):
        print("Creating all tables for the database...")
        db.create_all()
        if not CharacterModel.query.first():
            try:
                with open("characters.json", "r") as file:
                    characters_data = json.load(file)
                    for character_data in characters_data:
                        age = int(character_data["age"]) if character_data.get("age") else None
                        death = int(character_data["death"]) if character_data.get("death") else None
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

@app.route("/", methods=["GET"])
def home():
    """
    Home route that returns a welcome message.
    """
    return jsonify({"message": "Welcome to the Character API"}), 200

@app.route("/characters", methods=["GET"])
def get_characters():
    """
    Get a list of characters with optional filtering, sorting, and pagination.
    """
    limit = request.args.get("limit", type=int)
    skip = request.args.get("skip", type=int)
    sort_by = request.args.get("sort_by", type=str)
    order = request.args.get("order", "asc", type=str)

    filters = {}
    for key, value in request.args.items():
        if key not in ["limit", "skip", "sort_by", "order"]:
            filters[key] = value

    valid_filter_fields = ['age', 'name', 'house', 'role', 'strength']
    query = CharacterModel.query

    for key, value in filters.items():
        if key == "age_more_than":
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
                query = query.filter(getattr(CharacterModel, key).ilike(f"%{value}%"))
        else:
            return jsonify({"error": f"Invalid filter attribute: {key}"}), 400

    valid_sort_fields = ['name', 'house', 'role', 'age', 'strength', 'id']
    if sort_by and sort_by in valid_sort_fields:
        if order == "asc":
            query = query.order_by(getattr(CharacterModel, sort_by).asc())
        else:
            query = query.order_by(getattr(CharacterModel, sort_by).desc())
    else:
        query = query.order_by(CharacterModel.id.asc())

    if limit is None and skip is None:
        limit = 20
        characters_query = query.limit(limit).all()
    else:
        if skip is None:
            skip = 0
        if limit is None:
            characters_query = query.offset(skip).all()
        else:
            characters_query = query.offset(skip).limit(limit).all()

    characters_list = [character.to_dict() for character in characters_query]
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
    data = request.json
    required_fields = ["name", "role", "age", "strength"]

    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    if not isinstance(data["age"], int):
        return jsonify({"error": "'age' must be an integer"}), 400
    if not isinstance(data["name"], str):
        return jsonify({"error": "'name' must be a string"}), 400

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

@app.route("/characters/<int:id>", methods=["PATCH"])
def edit_character(id):
    """
    Edit an existing character by its ID.
    """
    character = CharacterModel.query.get(id)
    if not character:
        return jsonify({"error": "Character not found"}), 404

    data = request.json
    fields = ['name', 'house', 'animal', 'symbol', 'nickname', 'role', 'age', 'death', 'strength']

    for field in fields:
        if field in data:
            setattr(character, field, data[field])

    db.session.commit()
    return jsonify({"message": "Character updated"}), 200

@app.route("/characters/<int:id>", methods=["DELETE"])
def delete_character(id):
    """
    Delete a character by its ID.
    """
    character = CharacterModel.query.get(id)
    if not character:
        return jsonify({"error": "Character not found"}), 404

    db.session.delete(character)
    db.session.commit()
    return jsonify({"message": "Character deleted"}), 200

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
    setup_database()
    app.run(debug=True)