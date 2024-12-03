from utils import is_token_revoked, schedule_auto_invest, schedule_subscription
from models import Subscription, Transaction, User
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask import Blueprint, request, jsonify
from extensions import db
from flask import current_app

subscription_routes_bp = Blueprint("subscription_routes", __name__)


@subscription_routes_bp.route("/api/user-actions/subscribe", methods=["POST"])
@jwt_required()
def create_subscription():
    try:
        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        # Check if user exists
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if user is None:
            return jsonify({"message": "Incorrect user"}), 400

        data = request.get_json()

        # Check if data has been parsed
        if not data:
            return jsonify({"message": "No data provided"}), 400

        # Check if missing fields
        required_fields = ["pin", "amount", "intervalSeconds"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        pin = data.get("pin")
        amount = float(data.get("amount"))
        interval_seconds = int(data.get("intervalSeconds"))

        # Check if PIN is correct
        if user.pin != pin:
            return jsonify({"message": "Invalid PIN."}), 401

        # Validate subscription amount
        if amount <= 0:
            return jsonify({"message": "Invalid amount."}), 400

        # Check for sufficient funds
        if amount > user.account.balance:
            return jsonify({"message": "Insufficient funds"}), 400

        subscription = Subscription(
            user_id=user.id, amount=amount, interval_seconds=interval_seconds
        )

        db.session.add(subscription)
        db.session.commit()

        # Fetch the latest subscription to get the job_id
        latest_subscription = (
            Subscription.query.filter_by(user_id=user.id)
            .order_by(Subscription.id.desc())
            .first()
        )

        if latest_subscription:
            # Schedule subscription
            schedule_subscription(
                app=current_app._get_current_object(),
                user_id=user.id,
                amount=amount,
                interval_seconds=interval_seconds,
                job_id=latest_subscription.job_id,
            )

        return jsonify({"message": "Subscription created successfully"}), 201

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@subscription_routes_bp.route("/api/account/enable-auto-invest", methods=["POST"])
@jwt_required()
def enable_auto_invest():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"message": "User not found"}), 400

        # Check if data has been parsed
        data = request.get_json()

        if not data:
            return jsonify({"message": "No data provided"}), 400

        pin = data.get("pin")

        # Check if PIN is correct
        if user.pin != pin:
            return jsonify({"message": "Invalid PIN."}), 401

        # Enable auto-invest bot
        user.auto_invest_enabled = True
        db.session.commit()
        schedule_auto_invest(app=current_app._get_current_object(), user_id=user.id)

        return jsonify({"message": "Automatic investment enabled successfully."}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@subscription_routes_bp.route("/api/account/disbale-auto-invest", methods=["POST"])
@jwt_required()
def disable_auto_invest():

    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"message": "User not found"}), 400

        # Check if data has been parsed
        data = request.get_json()

        if not data:
            return jsonify({"message": "No data provided"}), 400

        pin = data.get("pin")

        # Check if PIN is correct
        if user.pin != pin:
            return jsonify({"message": "Invalid PIN."}), 401

        # Disable auto-invest bot
        user.auto_invest_enabled = False
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Automatic investment disabled successfully."
                }
            ),
            200,
            )

    except Exception as e:
        return jsonify({"message": str(e)}), 500
