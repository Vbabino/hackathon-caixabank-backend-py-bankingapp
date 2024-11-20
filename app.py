from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from models import  User  
from dotenv import load_dotenv
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
@app.route('/')
def index():
    return "Flask app is running!"

# Endpoint to register a new user
@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        # Validate input data
        if not name or not email or not password:
            return jsonify({"message": "All fields are required."}), 400

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already registered."}), 400

        # Create a new user
        new_user = User(name=name, email=email)
        new_user.set_password(password)

        # Save to the database
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "name": new_user.name,
            "email": new_user.email,
            "id": new_user.id
        }), 201
    except Exception as e:
        print("Error:", e)  # Debug line for errors
        return jsonify({"message": "Internal Server Error"}), 500

# Endpoint for user login
@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Check if the user exists
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"message": "Invalid credentials."}), 401

    # Create a JWT token
    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token}), 200



if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=3000, debug=True)
