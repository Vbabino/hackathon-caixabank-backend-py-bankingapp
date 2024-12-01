from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from extensions import db

from models import Transaction, User
from utils import is_token_revoked

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/api/account/deposit", methods=["POST"])
@jwt_required()
def deposit():
    try:
        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        # Check if user exists
        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if user is None:
            return (
                jsonify({"message": "Incorrect user"}),
                400,
            )

        # Check if data has been parsed
        data = request.get_json()

        if not data:
            return (
                jsonify({"message": "No data provided"}),
                400,
            )

        # Validate input data
        required_fields = ["pin", "amount"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        pin = data.get("pin")
        amount = data.get("amount")

        # Check if PIN is correct

        if user.pin != pin:
            return jsonify({"message": "Invalid PIN."}), 401

        # Validate deposit amount
        if amount <= 0:
            return jsonify({"msg": "Deposit amount must be greater than 0"}), 400

        user.account.balance += amount

        # Create a transaction record
        new_transaction = Transaction(
            user_id=user.id,
            amount=amount,
            transaction_type="CASH_DEPOSIT",
            source_account_number=user.accountNumber,
            target_account_number="N/A",
        )
        db.session.add(new_transaction)

        db.session.commit()

        return jsonify({"msg": "Cash deposited successfully"})

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@transactions_bp.route("/api/account/withdraw", methods=["POST"])
@jwt_required()
def withdraw():
    try:
        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        # Check if user exists
        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if user is None:
            return (
                jsonify({"message": "Incorrect user"}),
                400,
            )

        # Check if data has been parsed
        data = request.get_json()

        if not data:
            return (
                jsonify({"message": "No data provided"}),
                400,
            )

        # Validate input data
        required_fields = ["pin", "amount"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        pin = data.get("pin")
        amount = data.get("amount")

        # Check if PIN is correct

        if user.pin != pin:
            return jsonify({"message": "Invalid PIN."}), 401

        # Validate withdraw amount
        if amount <= 0:
            return jsonify({"msg": "Withdraw amount must be greater than 0"}), 400

        if amount >= user.account.balance:
            return jsonify({"msg": "Insufficient funds"})

        user.account.balance -= amount

        # Create a transaction record
        new_transaction = Transaction(
            user_id=user.id,
            amount=amount,
            transaction_type="CASH_WITHDRAWAL",
            source_account_number=user.accountNumber,
            target_account_number="N/A",
        )
        db.session.add(new_transaction)

        db.session.commit()

        return jsonify({"msg": "Cash withdrawn successfully"})

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@transactions_bp.route("/api/account/fund-transfer", methods=["POST"])
@jwt_required()
def fund_transfer():
    try:
        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        # Check if user exists
        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if user is None:
            return (
                jsonify({"message": "Incorrect user"}),
                400,
            )

        # Check if data has been parsed
        data = request.get_json()

        if not data:
            return (
                jsonify({"message": "No data provided"}),
                400,
            )

        # Validate input data
        required_fields = ["pin", "amount", "targetAccountNumber"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        pin = data.get("pin")
        amount = data.get("amount")
        targetAccountNumber = data.get("targetAccountNumber")

        # Check if PIN is correct

        if user.pin != pin:
            return jsonify({"message": "Invalid PIN."}), 401

        # Validate amount
        if amount <= 0:
            return jsonify({"msg": "Amount must be greater than 0"}), 400

        if amount > user.account.balance:
            return jsonify({"msg": "Insufficient funds"})

        # Fetch target account user
        target_account_user = User.query.filter_by(
            accountNumber=targetAccountNumber
        ).first()

        # Check if taget account exists
        if not target_account_user:
            return jsonify({"message": "Target account does not exist."}), 400

        # Perform fund transfer
        user.account.balance -= amount
        target_account_user.account.balance += amount

        # Create a transaction record for source account
        transaction_source_account = Transaction(
            user_id=user.id,
            amount=amount,
            transaction_type="CASH_TRANSFER",
            source_account_number=user.accountNumber,
            target_account_number=target_account_user.accountNumber,
        )
        # Create a transaction record for target account
        transaction_target_account = Transaction(
            user_id=target_account_user.id,
            amount=amount,
            transaction_type="CASH_TRANSFER",
            source_account_number=user.accountNumber,
            target_account_number=target_account_user.accountNumber,
        )
        db.session.add(transaction_source_account)
        db.session.add(transaction_target_account)

        db.session.commit()

        return jsonify({"msg": "Fund transferred successfully"})

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@transactions_bp.route("/api/account/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    try:
        # Check if token has been revoked
        jti = get_jwt()["jti"]

        if is_token_revoked(jti):
            return jsonify({"message": "Session has expired"}), 401

        user_id = get_jwt_identity()

        user = User.query.get(user_id)

        if not user:
            return jsonify({"message": "User not found"}), 404

        transaction_list = [
            {
                "id": transaction.id,
                "amount": transaction.amount,
                "transactionType": transaction.transaction_type,
                "transactionDate": transaction.transaction_date,
                "sourceAccountNumber": transaction.source_account_number,
                "targetAccountNumber": transaction.target_account_number,
            }
            for transaction in user.transactions
        ]

        return jsonify({"transaction_list": transaction_list})

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500
