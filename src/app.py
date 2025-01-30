"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Language, Word
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


@app.route('/languages', methods=['GET'])
def get_languajes():
    all_languages = list(Language.query.all())
    results = list(map(lambda language: language.serialize(), all_languages))
    return jsonify(results), 200


@app.route("/language/create", methods=["POST"])
def create_language():
    body = request.get_json()

    if "name" not in body:
        return jsonify({"msg": "Faltan datos requeridos"}), 400

    language_name = body["name"].upper()

    existing_language = Language.query.filter_by(name=language_name).first()
    if existing_language:
        return jsonify({"msg": "El lenguaje ya existe"}), 409

    language = Language(name=language_name)
    db.session.add(language)
    db.session.commit()

    response_body = {
        "msg": "Lenguaje creado",
        "result": language.serialize()
    }
    return jsonify(response_body), 201

@app.route('/words', methods=['GET'])
def get_words():
    all_words = list(Word.query.all())
    results = list(map(lambda words: words.serialize(), all_words))
    return jsonify(results), 200


@app.route("/word/create", methods=["POST"])
def create_word():
    body = request.get_json()

    if "word" not in body or "definition" not in body or "language_id" not in body:
        return jsonify({"msg": "Faltan datos requeridos"}), 400


    word = body["word"].upper()
 
    existing_word = Word.query.filter_by(word=word).first()
    if existing_word:
        return jsonify({"msg": "La palabra ya existe"}), 409

    language = Language.query.get(body["language_id"])
    if not language:
        return jsonify({"msg": "El lenguaje especificado no existe"}), 400

    new_word = Word(
        word=word,
        definition=body["definition"],
        language_id=body["language_id"]
    )

    db.session.add(new_word)
    db.session.commit()

    response_body = {
        "msg": "Palabra creada",
        "result": new_word.serialize()
    }
    return jsonify(response_body), 201


@app.route('/words/language/<int:language_id>', methods=['GET'])
def get_words_of_language(language_id):
    language = Language.query.get(language_id)
    if not language:
        return jsonify({"msg": "El lenguaje especificado no existe"}), 404

    words_language = Word.query.filter_by(language_id=language_id).all()

    if not words_language:
        return jsonify({"msg": "Aún no hay palabras registradas para este lenguaje"}), 200

    response_data = [word.serialize() for word in words_language]

    return jsonify(response_data), 200

@app.route('/word/<string:language>/<string:word>', methods=['GET'])
def get_word_by_language(language , word):
    language_in_db = Language.query.filter_by(name=language.upper()).first()

    if not language_in_db:
       return jsonify({"msg": "El lenguaje especificado no existe"}), 404
    
    word_in_db = Word.query.filter_by(word=word.upper(), language_id= language_in_db.id).first()

    if not word_in_db:
       return jsonify({"msg": "La palabra especificada no existe"}), 404


    return jsonify(word_in_db.serialize()), 200

@app.route('/word/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    word_to_delete = Word.query.get(word_id)
    if word_to_delete:
        db.session.delete(word_to_delete)
        db.session.commit()
        response_body = {"msg": "Se eliminó correctamente"}
    else:
        response_body = {"msg": "No se encontró la palabra"}
    return jsonify(response_body), 200

@app.route('/word/<int:word_id>', methods=['PUT'])
def update_word(word_id):
    body = request.get_json()
    word_to_edit = Word.query.filter_by(id=word_id).first()
    if word_to_edit is None:
        return jsonify({"error": "Palabra no encontrada"}), 404

    if "word" in body:
        word_to_edit.word = body["word"]
    if "definition" in body:
        word_to_edit.definition = body["definition"]
    if "language_id" in body:
        language = Language.query.filter_by(id=body["language_id"]).first()
        if language is None:
            return jsonify({"error": "Lenguaje no encontrado"}), 404
        else: 
            word_to_edit.language_id = body["language_id"]

    db.session.commit()

    return jsonify({"msg": "Se actualizado con éxito", "word": word_to_edit.serialize()}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
