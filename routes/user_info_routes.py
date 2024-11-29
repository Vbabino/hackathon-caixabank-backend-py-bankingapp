from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from models import User
from utils import is_token_revoked

user_bp = Blueprint("user", __name__)


# Endpoint to retrive the logged-in user's details
@user_bp.route("/api/dashboard/user", methods=["GET"])
@jwt_required()
def user_info():
    try:
        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if not user:
            return jsonify({"message": "User not found"}), 404

        return (
            jsonify(
                {
                    "name": user.name,
                    "email": user.email,
                    "phoneNumber": user.phoneNumber,
                    "address": user.address,
                    "accountNumber": user.accountNumber,
                    "hashedPassword": user.password_hash,
                }
            ),
            200,
        )

    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Internal Server Error"}), 500


@user_bp.route("/api/dashboard/account", methods=["GET"])
@jwt_required()
def account_info():
    try:
        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if not user:
            return jsonify({"message": "Access Denied"}), 401

        return (
            jsonify(
                {
                    "accountNumber": user.accountNumber,
                    "balance": user.account.balance,
                }
            ),
            200,
        )
    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Internal Server Error"}), 500
