#!/usr/bin/env python3

from models import db, Activity, Camper, Signup
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import Flask, make_response, jsonify, request, abort
import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


class Campers(Resource):
    def get(self):
        campers = [camper.to_dict() for camper in Camper.query.all()]

        for camper in campers:
            del camper["signups"]

        return make_response(campers, 200)

    def post(self):
        request_json = request.get_json()
        try:
            new_camper = Camper(name=request_json["name"], age=request_json["age"])

            db.session.add(new_camper)
            db.session.commit()
            new_camper_dict = new_camper.to_dict(only=("id", "name", "age"))
            return make_response(new_camper_dict, 201)

        except ValueError:
            return make_response({"errors": ["validation errors"]}, 400)


api.add_resource(Campers, "/campers")


class CamperByID(Resource):
    def get(self, id):
        camper = Camper.query.filter(Camper.id == id).first()

        if not camper:
            return make_response({"error": "Camper not found"}, 404)

        return make_response(camper.to_dict(), 200)

    def patch(self, id):
        camper = Camper.query.filter(Camper.id == id).first()

        if not camper:
            return make_response({"error": "Camper not found"}, 404)

        request_json = request.get_json()

        try:
            for key in request_json:
                setattr(camper, key, request_json[key])

            db.session.add(camper)
            db.session.commit()
            camper_dict = camper.to_dict()
            del camper_dict["signups"]
            return make_response(camper_dict, 202)
        except ValueError:
            return make_response({"errors": ["validation errors"]}, 400)


api.add_resource(CamperByID, "/campers/<int:id>")


class Activities(Resource):
    def get(self):
        activities = [
            activity.to_dict(rules=("-signups",)) for activity in Activity.query.all()
        ]

        return make_response(activities, 200)


api.add_resource(Activities, "/activities")


class ActivityByID(Resource):
    def delete(self, id):
        activity = Activity.query.filter(Activity.id == id).first()

        if not activity:
            return make_response({"error": "Activity not found"}, 404)

        db.session.delete(activity)
        db.session.commit()

        return make_response("Successfully deleted", 204)


api.add_resource(ActivityByID, "/activities/<int:id>")


class Signups(Resource):
    def post(self):
        request_json = request.get_json()
        try:
            new_signup = Signup(
                camper_id=request_json["camper_id"],
                activity_id=request_json["activity_id"],
                time=request_json["time"],
            )
            db.session.add(new_signup)
            db.session.commit()
            return make_response(new_signup.to_dict(), 201)

        except ValueError:
            return make_response({"errors": ["validation errors"]}, 400)


api.add_resource(Signups, "/signups")
if __name__ == "__main__":
    app.run(port=5555, debug=True)
