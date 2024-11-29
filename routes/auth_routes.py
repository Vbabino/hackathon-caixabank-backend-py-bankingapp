from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from extensions import *
from utils import *

# Create a blueprint
auth_bp = Blueprint("auth", __name__)


# Endpoint to register a new user
@auth_bp.route("/api/users/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        address = data.get("address")
        phoneNumber = data.get("phoneNumber")

        # Validate input data
        required_fields = ["name", "email", "password", "address", "phoneNumber"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already registered."}), 400

        # Check if phone number already exists
        if User.query.filter_by(phoneNumber=phoneNumber).first():
            return jsonify({"message": "Phone number already registered."}), 400

        # Create a new user
        new_user = User(
            name=name, email=email, phoneNumber=phoneNumber, address=address
        )
        new_user.set_password(password)

        # Create a new account associated with the user
        new_account = Account(user_id=new_user.id, balance=0.0)
        new_user.account = new_account  # Establish relationship

        # Save to the database
        db.session.add(new_user)
        db.session.add(new_account)
        db.session.commit()

        return (
            jsonify(
                {
                    "name": new_user.name,
                    "email": new_user.email,
                    "phoneNumber": new_user.phoneNumber,
                    "address": new_user.address,
                    "accountNumber": new_user.accountNumber,
                    "hashedPassword": new_user.password_hash,
                }
            ),
            201,
        )
    except Exception as e:
        print("Error:", e)  # Debug line for errors
        return jsonify({"message": "Internal Server Error"}), 500


# Endpoint for user login
@auth_bp.route("/api/users/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Check if the user exists
    user = User.query.filter_by(email=email).first()

    if user is None:
        return (
            jsonify({"message": "User not found for the given identifier: " + email}),
            400,
        )

    if not user.check_password(password):
        return jsonify({"message": "Bad credentials"}), 401

    # Create a JWT token
    access_token = create_access_token(identity=str(user.id))
    return jsonify({"token": access_token}), 200


@auth_bp.route("/api/users/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    revoked_token = RevokedToken(token=jti)
    db.session.add(revoked_token)
    db.session.commit()
    return (jsonify({"message": "Successfully logged out"})), 200
