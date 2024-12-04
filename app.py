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
    print("Creates all tables for the database...")
    db.create_all()  # Creates all tables if they do not already exist
    if not CharacterModel.query.first():  # checking by looking for first entry, and only populate the database if it is empty
        try:
            with open("characters.json", "r") as file:
                characters_data = json.load(file)

                for character_data in characters_data:

                    # Convert age and death to integers if they exist, else set to None
                    age = int(character_data["age"]) if character_data.get("age") else None
                    death = int(character_data["death"]) if character_data.get("death") else None

                    # we go through the characters in the json file and grab the data
                    # instantiating an object of the CharacterModel class for each character
                    character_obj = CharacterModel(
                        # mandatory, will raise error if not existing
                        id=character_data["id"],
                        name=character_data["name"],
                        # if does not exist will be None
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

    # getting the query parameters from the request
    # we will use to filter, sort and paginate the data
    # e.g.
    # /characters?limit=10&skip=0&sort_by=age&order=asc&name=Jon%20Snow&age_more_than=20
    # http://127.0.0.1:5000/characters?limit=5&skip=1&sort_by=age&order=asc&house=Stark
    limit = request.args.get("limit", type=int)
    skip = request.args.get("skip", type=int)
    sort_by = request.args.get("sort_by", type=str)
    order = request.args.get("order", "asc", type=str)

    # create a dictionary of filters from the request arguments
    # to be used in the query.filter() method below
    filters = {}
    for key, value in request.args.items():
        if key not in ["limit", "skip", "sort_by", "order"]:
            filters[key] = value

    valid_filter_fields = ['name', 'house', 'role', 'age', 'strength']

    query = CharacterModel.query   # to be able to filter, sort and paginate the data
    
    # Apply filters
    for key, value in filters.items():
        if key == "age_more_than":
            query = query.filter(CharacterModel.age >= int(value))
        elif key == "age_less_than":
            query = query.filter(CharacterModel.age <= int(value))
        elif key in valid_filter_fields:
            query = query.filter(getattr(CharacterModel, key) == value)
        else:
            return jsonify({"error": f"Invalid filter attribute: {key}"}), 400


    # Apply sorting
    if sort_by:
        if order == "asc":
            if sort_by == "name":
                query = query.order_by(CharacterModel.name.asc())
            elif sort_by == "house":
                query = query.order_by(CharacterModel.house.asc())
            elif sort_by == "age":
                query = query.order_by(CharacterModel.age.asc())
        else:
            if sort_by == "name":
                query = query.order_by(CharacterModel.name.desc())
            elif sort_by == "house":
                query = query.order_by(CharacterModel.house.desc())
            elif sort_by == "age":
                query = query.order_by(CharacterModel.age.desc())

    # Apply pagination when limit and skip are given
    if limit is None and skip is None:
        characters = query.all()
        random_characters = random.sample(characters, min(20, len(characters)))
        characters_list = []
        
        # Convert the characters to a dictionary so we can jsonify them later
        for character in random_characters:
            characters_list.append(character.to_dict())
            
            
    # default pagination:
    # if limit is not given, default to 20;
    # if skip is not given, default to 0
    else:
        if skip is None:
            skip = 0
        if limit is None:
            limit = 20
        characters_query = query.offset(skip).limit(limit).all()
        
        characters_list = []
        
        for character in characters_query:
            characters_list.append(character.to_dict())
    
        return jsonify(characters_list), 200



if __name__ == "__main__":
    app.run(debug=True)