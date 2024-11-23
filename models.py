import uuid
from datetime import datetime, timezone, timedelta
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
    reset_token = db.Column(db.String(36), nullable=True)
    pin = db.Column(db.String(4), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship("Account", back_populates="user", uselist=False)

    # Hash the password
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # Verify the password
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", back_populates="account")


class RevokedToken(db.Model):
    __tablename__ = "revoked_tokens"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500), unique=True, nullable=True)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)


class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    current_datetime = db.Column(db.DateTime, nullable=True)

    def is_valid(self):

        if self.current_datetime:
            # Ensure both are offset-aware
            current_dt = self.current_datetime.replace(tzinfo=timezone.utc)
            expires_at = self.expires_at.replace(tzinfo=timezone.utc)  # Convert to UTC
            return current_dt < expires_at
        return False
