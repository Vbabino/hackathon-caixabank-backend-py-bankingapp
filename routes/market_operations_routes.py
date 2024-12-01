from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import func
from extensions import db
from models import Asset, Transaction, User
from utils import is_token_revoked, get_market_price, send_investment_confirmation_email, send_investment_sale_confirmation_email

market_operations_bp = Blueprint("market_operations", __name__)


@market_operations_bp.route("/api/account/buy-asset", methods=["POST"])
@jwt_required()
def buy_asset():
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

        # Check if data has been parsed
        data = request.get_json()

        if not data:
            return jsonify({"message": "No data provided"}), 400

        # Validate input data
        required_fields = ["pin", "assetSymbol", "amount"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        pin = data.get("pin")
        asset_symbol = data.get("assetSymbol")
        amount = data.get("amount")

        # Check if PIN is correct
        if user.pin != pin:
            return jsonify({"message": "Invalid PIN."}), 401

        # Validate purchase amount
        if amount <= 0:
            return jsonify({"message": "Invalid amount."}), 400

        # Check for sufficient funds
        if amount > user.account.balance:
            return jsonify({"message": "Insufficient funds"}), 400

        # Fetch market prices
        market_prices = get_market_price()

        # Check asset symbol exists
        if asset_symbol not in market_prices:
            return jsonify({"message": "Asset not found"}), 404

        # Perform asset purchase
        purchase_price = market_prices[asset_symbol]
        units_purchased = amount / purchase_price

        user.account.balance -= amount

        new_asset_purchase = Asset(
            user_id=user.id,
            asset_symbol=asset_symbol,
            amount=amount,
            purchase_price=purchase_price,
            quantity=units_purchased,
        )

        # Create a transaction record
        new_transaction = Transaction(
            user_id=user.id,
            amount=amount,
            transaction_type="ASSET_PURCHASE",
            source_account_number=user.accountNumber,
        )
        
        db.session.add(new_transaction)
        db.session.add(new_asset_purchase)
        db.session.commit()

        # Query the total quantity of the given asset symbol
        current_holdings = (
            db.session.query(func.sum(Asset.quantity))
            .filter_by(user_id=user.id, asset_symbol=asset_symbol)
            .scalar()
        )

        # Send email confirmation
        send_investment_confirmation_email(
            user=user,
            units_purchased=units_purchased,
            asset_symbol=asset_symbol,
            amount=amount,
            current_holdings=current_holdings,
            purchase_price=purchase_price,
            balance=user.account.balance,
        )

        return jsonify({"message": "Asset purchased successfully"}), 201

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500


@market_operations_bp.route("/api/account/sell-asset", methods=["POST"])
@jwt_required()
def sell_asset():
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

        # Check if data has been parsed
        data = request.get_json()

        if not data:
            return jsonify({"message": "No data provided"}), 400

        # Validate input data
        required_fields = ["pin", "assetSymbol", "quantity"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}), 400

        pin = data.get("pin")
        asset_symbol = data.get("assetSymbol")
        quantity = data.get("quantity")

        # Check if PIN is correct
        if user.pin != pin:
            return jsonify({"message": "Invalid PIN."}), 401

        # Validate quantity
        if quantity <= 0:
            return jsonify({"message": "Invalid quantity."}), 400

        # Check if user has the asset
        asset = Asset.query.filter_by(user_id=user.id, asset_symbol=asset_symbol).first()

        if asset is None:
            return jsonify({"message": "Asset not found"}), 404

        # Check if user has enough quantity to sell
        if quantity > asset.quantity:
            return jsonify({"message": "Insufficient quantity"}), 400

        # Fetch market prices
        market_prices = get_market_price()

        # Check asset symbol exists
        if asset_symbol not in market_prices:
            return jsonify({"message": "Asset not found"}), 404

        # Perform asset sale
        sell_price = market_prices[asset_symbol]
        total_sale_value = quantity * sell_price

        user.account.balance += total_sale_value
        asset.quantity -= quantity

        # Create a transaction record
        new_transaction = Transaction(
            user_id=user.id,
            amount=total_sale_value,
            transaction_type="ASSET_SELL",
            source_account_number=user.accountNumber,
            target_account_number="N/A",
        )

        db.session.add(new_transaction)
        db.session.commit()

        # Query the total quantity of the given asset symbol
        current_holdings = db.session.query(func.sum(Asset.quantity)).filter_by(user_id=user.id, asset_symbol=asset_symbol).scalar()

        total_gain_loss = total_sale_value - (quantity * asset.purchase_price)

        # Send email confirmation
        send_investment_sale_confirmation_email(
            user=user,
            units_sold=quantity,
            asset_symbol=asset_symbol,
            gain_loss=total_gain_loss,
            current_holdings=current_holdings,
            purchase_price=asset.purchase_price,
            balance=user.account.balance
        )

        return jsonify({"message": "Asset sold successfully"}), 200

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@market_operations_bp.route("/market/prices", methods=["GET"])
def market_prices():
    try:
        market_prices = get_market_price()
        return jsonify(market_prices), 200

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@market_operations_bp.route("/market/prices/<symbol>", methods=["GET"])
def market_price(symbol):
    try:
        market_prices = get_market_price()
        price = market_prices.get(symbol)

        if price is None:
            return jsonify({"message": "Asset not found"}), 404

        return jsonify({symbol: price}), 200

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500