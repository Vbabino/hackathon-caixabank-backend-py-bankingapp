from flask import Flask
from dotenv import load_dotenv

import os
from extensions import *

from routes.auth_routes import auth_bp
from routes.user_info_routes import user_bp
from routes.password_reset_routes import otp_bp
from routes.pin_routes import pin_bp
from routes.transactions_routes import transactions_bp

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


app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(otp_bp)
app.register_blueprint(pin_bp)
app.register_blueprint(transactions_bp)


# Placeholder route for testing
@app.route("/")
def index():
    return "Flask app is running!"


if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(host="0.0.0.0", port=3000, debug=True)
