import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from extensions import *
from models import User
from utils import is_token_revoked


pin_bp = Blueprint("pin", __name__)


@pin_bp.route("/api/account/pin/create", methods=["POST"])
@jwt_required()
def create_pin():

    try:
        data = request.get_json()
        pin = data.get("pin")
        password = data.get("password")

        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        if not re.match(r"^\d{4}$", pin):
            return jsonify({"error": "PIN must be 4 digits."}), 400

        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if user is None:
            return (
                jsonify({"message": "Incorrect user"}),
                400,
            )

        if not user.check_password(password):
            return jsonify({"message": "Bad credentials"}), 401

        user.pin = pin
        db.session.commit()

        return jsonify({"message": "PIN created successfully"}), 201

    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Internal Server Error"}), 500


@pin_bp.route("/api/account/pin/update", methods=["POST"])
@jwt_required()
def update_pin():

    try:
        data = request.get_json()
        old_pin = data.get("oldPin")
        password = data.get("password")
        new_pin = data.get("newPin")

        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        required_fields = ["oldPin", "password", "newPin"]

        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if user is None:
            return (
                jsonify({"message": "Incorrect user"}),
                400,
            )

        if user.pin != old_pin:
            return jsonify({"message": "Incorrect old PIN"}), 401

        if not user.check_password(password):
            return jsonify({"message": "Bad credentials"}), 401

        if not re.match(r"^\d{4}$", new_pin):
            return jsonify({"error": "PIN must be 4 digits."}), 400

        user.pin = new_pin
        db.session.commit()

        return jsonify({"message": "PIN created successfully"}), 201

    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Internal Server Error"}), 500
