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
from models import db, User, Language
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


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
