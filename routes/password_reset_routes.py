import datetime
import random
import uuid
from flask import Blueprint, request, jsonify
from extensions import *

from models import OTP, User
from utils import send_email
from flasgger.utils import swag_from

otp_bp = Blueprint("otp", __name__)


@otp_bp.route("/api/auth/password-reset/send-otp", methods=["POST"])
@swag_from("docs/send_otp.yml")
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


@otp_bp.route("/api/auth/password-reset/verify-otp", methods=["POST"])
@swag_from("docs/verify_otp.yml")
def verify_otp():
    data = request.get_json()
    identifier = data.get("identifier")
    otp = data.get("otp")

    otp_code = OTP.query.filter_by(identifier=identifier, otp=otp).first()
    user = User.query.filter_by(email=identifier).first()

    if not otp_code:
        return jsonify({"error": "Invalid OTP."}), 400

    otp_code.current_datetime = datetime.now(datetime.timezone.utc)

    if not otp_code.is_valid():
        return jsonify({"error": "Invalid OTP."}), 400

    password_reset_token = str(uuid.uuid4())
    user.reset_token = password_reset_token
    db.session.commit()

    return jsonify({"passwordResetToken": password_reset_token}), 200


@otp_bp.route("/auth/password-reset", methods=["POST"])
@swag_from("docs/reset_password.yml")
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
