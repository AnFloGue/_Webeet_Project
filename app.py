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


class CharacterModel(db.Model):
    """
    This class represents the Character table in the database.
    Each instance of this class corresponds to a row in the table.
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
        Convert the CharacterModel object to a dictionary.
        This is useful for converting the object to JSON format.
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
    This function sets up the database before handling any request.
    It creates all tables if they do not already exist and populates the database with initial data.
    """
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

        # we avoid reinitializing the database so that the data is not being duplicated
        app.db_initialized = True


@app.route("/characters", methods=["GET"])
def get_characters():
    """
    This function handles GET requests to the /characters endpoint.
    It retrieves characters from the database with optional filtering, sorting, and pagination.
    """
    limit = request.args.get("limit", type=int)
    skip = request.args.get("skip", type=int)
    sort_by = request.args.get("sort_by", type=str)
    order = request.args.get("order", "asc", type=str)

    filters = {}
    # Get all parameters in the request that are not limit, skip, sort_by, or order and
    # add them to the filters dictionary so that we can filter the query. With this,
    # we can apply these filters to the database query and get the requested data.
    for key, value in request.args.items():
        if key not in ["limit", "skip", "sort_by", "order"]:
            filters[key] = value

    valid_filter_fields = ['age', 'name', 'house', 'role', 'strength']

    query = CharacterModel.query

    for key, value in filters.items():
        if key == "age_more_than":  # query parameter that should come from the request URL
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

    valid_sort_fields = ['name', 'house', 'role', 'age', 'strength']
    if sort_by and sort_by in valid_sort_fields:
        if order == "asc":
            query = query.order_by(getattr(CharacterModel, sort_by).asc())
        else:
            query = query.order_by(getattr(CharacterModel, sort_by).desc())

    # If limit is not provided, return 20 random characters
    if limit is None and skip is None:
        limit = 20
        characters_query = query.all()
        random.shuffle(characters_query)
        characters_query = characters_query[:limit]

    # If limit is not provided but skip is, return all characters after the skip
    else:
        if skip is None:
            skip = 0
        if limit is None:
            characters_query = query.offset(skip).all()
        else:
            characters_query = query.offset(skip).limit(limit).all()

    characters_list = []
    for character in characters_query:
        characters_list.append(character.to_dict())

    return jsonify(characters_list), 200


@app.route("/characters/<int:id>", methods=["GET"])
def get_character_by_id(id):
    """
    This function handles GET requests to the /characters/<id> endpoint.
    It retrieves a character by its ID from the database.
    """
    character = CharacterModel.query.get(id)

    if not character:
        return jsonify({"error": "Character not found"}), 404

    return jsonify(character.to_dict()), 200


@app.route("/characters", methods=["POST"])
def add_character():
    """
    This function handles POST requests to the /characters endpoint.
    It adds a new character to the database.
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


@app.route("/characters/<int:id>", methods=["PATCH"])
def edit_character(id):
    """
    This function handles PATCH requests to the /characters/<id> endpoint.
    It updates an existing character in the database.
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


@app.route("/characters/<int:id>", methods=["DELETE"])
def delete_character(id):
    """
    This function handles DELETE requests to the /characters/<id> endpoint.
    It deletes an existing character from the database.
    """
    # Get the character by ID
    character = CharacterModel.query.get(id)

    # Check if the character exists
    if not character:
        return jsonify({"error": "Character not found"}), 404

    db.session.delete(character)
    db.session.commit()
    return jsonify({"message": "Character deleted"}), 200


@app.errorhandler(400)
def bad_request(error):
    """
    This function handles 400 Bad Request errors.
    """
    return jsonify({"error": "Bad Request"}), 400


@app.errorhandler(404)
def not_found(error):
    """
    This function handles 404 Not Found errors.
    """
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(500)
def internal_server_error(error):
    """
    This function handles 500 Internal Server Error errors.
    """
    if app.debug:
        return jsonify({"error": str(error)}), 500
    else:
        return jsonify({"error": "Internal Server Error"}), 500


if __name__ == "__main__":
    setup_database()
    app.run(debug=True)