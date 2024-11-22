import random
from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, get_jwt_identity
from models import *
from dotenv import load_dotenv
from utils import *
import os
from extensions import *

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()


# Placeholder route for testing
@app.route("/")
def index():
    return "Flask app is running!"


# Endpoint to register a new user
@app.route("/api/users/register", methods=["POST"])
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
@app.route("/api/users/login", methods=["POST"])
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


# Endpoint to retrive the logged-in user's details
@app.route("/api/dashboard/user", methods=["GET"])
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


@app.route("/api/dashboard/account", methods=["GET"])
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

@app.route("/api/users/logout", methods=['POST'])
@jwt_required()
def logout():
    jti=get_jwt()['jti']
    revoked_token = RevokedToken(token=jti)
    db.session.add(revoked_token)
    db.session.commit()
    return (jsonify({"message": "Successfully logged out"})), 200

@app.route("/api/auth/password-reset/send-otp", methods=['POST'])
def send_otp():
    data = request.get_json()
    identifier = data.get("identifier")

    user = User.query.filter_by(email=identifier).first()
    if not user:
        return jsonify({"error": "User not found"}), 400

    otp = random.randint(100000, 999999)

    otp_entry = OTP(identifier=identifier, otp=str(otp))

    db.session.add(otp_entry)
    db.session.commit()

    send_email(identifier, otp)

    return (jsonify({"message": "OTP sent successfully to: " + identifier})), 200

@app.route("/api/auth/password-reset/verify-otp", methods=['POST'])
def verify_otp():
    data = request.get_json()
    identifier = data.get("identifier")
    otp = data.get("otp")

    otp_code = OTP.query.filter_by(identifier=identifier, otp=otp).first()
    user = User.query.filter_by(email=identifier).first()

    if not otp_code:
        return jsonify({"error": "Invalid OTP."}), 400

    otp_code.current_datetime = datetime.now(timezone.utc)

    if not otp_code.is_valid():
        return jsonify({"error": "Invalid OTP."}), 400

    password_reset_token = str(uuid.uuid4())
    user.reset_token = password_reset_token
    db.session.commit()

    return jsonify({"passwordResetToken": password_reset_token}), 200


@app.route("/auth/password-reset", methods=["POST"])
def reset_password():
    data = request.get_json()
    identifier = data.get("identifier")
    reset_token = data.get("resetToken")
    new_password = data.get("newPassword")

    user = User.query.filter_by(email=identifier).first()
    if not user:
        return jsonify({"error": "User not found."}), 404

    if user.reset_token != reset_token:
        return jsonify({"error": "Invalid reset token."}), 400

    user.set_password(new_password)

    user.reset_token = None
    db.session.commit()

    return jsonify({"message": "Password reset successfully"}), 200


if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(host="0.0.0.0", port=3000, debug=True)
