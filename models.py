import uuid
from datetime import datetime
from extensions import db, bcrypt


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phoneNumber = db.Column(db.String(15), unique=True, nullable=False)
    address = db.Column(db.String(120), nullable=False)
    accountNumber = db.Column(
        db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4())
    )
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship(
        "Account", back_populates="user", uselist=False
    )  

    # Hash the password
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Verify the password
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )  

    user = db.relationship("User", back_populates="account")
