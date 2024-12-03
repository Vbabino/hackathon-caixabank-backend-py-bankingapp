from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
from models import *
from sqlalchemy import exists, func
import smtplib
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()
scheduler.start()


def is_token_revoked(jti):
    token_revoked = db.session.query(exists().where(RevokedToken.token == jti)).scalar()
    return token_revoked


def validate_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))


def validate_password(password):
    if len(password) < 8 or len(password) > 128:
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char in "!@#$%^&*()-_=+[{]}\|;:'\",<.>/?`~" for char in password):
        return False
    if any(char.isspace() for char in password):
        return False
    return True


def send_email(to_email, otp):
    from_email = "CaixaBank@caixabank.com"
    subject = "Your OTP Code"
    body = f"OTP: {otp}"

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    smtp_server = "smtp"
    smtp_port = 1025

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.send_message(msg)


def get_market_price():
    url = "https://faas-lon1-917a94a7.doserverless.co/api/v1/web/fn-e0f31110-7521-4cb9-86a2-645f66eefb63/default/market-prices-simulator"
    response = requests.get(url)
    data = response.json()
    return data


def send_investment_confirmation_email(
    user,
    units_purchased,
    asset_symbol,
    amount,
    current_holdings,
    purchase_price,
    balance,
):
    """
    Sends an investment purchase confirmation email to the user.

    Parameters:
    - user: The user object containing user details.
    - units_purchased: The number of units of the asset purchased.
    - asset_symbol: The symbol of the asset purchased.
    - amount: The total amount spent on the purchase.
    - current_holdings: The total quantity of the asset the user holds after the purchase.
    - purchase_price: The price per unit of the asset at the time of purchase.
    - balance: The user's account balance after the purchase.

    The email includes details of the purchase, current holdings, and account balance.
    """

    from_email = "CaixaBank@caixabank.com"
    to_email = user.email
    subject = "Investment Purchase Confirmation"

    body = f"""
    Dear {user.name},

    You have successfully purchased {units_purchased:.2f} units of {asset_symbol} for a total amount of ${amount:.2f}.

    Current holdings of {asset_symbol}: {current_holdings:.2f} units

    Summary of current assets:
    - {asset_symbol}: {current_holdings:.2f} units purchased at ${purchase_price}

    Account Balance: ${balance:.2f}
    Net Worth: ${balance + (current_holdings * purchase_price):.2f}

    Thank you for using our investment services.

    Best Regards,
    Investment Management Team
    """

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    smtp_server = "smtp"
    smtp_port = 1025

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.send_message(msg)


def send_investment_sale_confirmation_email(
    user,
    units_sold,
    asset_symbol,
    gain_loss,
    current_holdings,
    purchase_price,
    balance,
):
    """
    Sends an investment sale confirmation email to the user.

    Parameters:
    - user: The user object containing user details.
    - units_sold: The number of units of the asset sold.
    - asset_symbol: The symbol of the asset sold.
    - current_holdings: The total quantity of the asset the user holds after the sale.
    - purchase_price: The price per unit of the asset at the time of purchase.
    - balance: The user's account balance after the sale.

    The email includes details of the sale, current holdings, and account balance.
    """

    from_email = "CaixaBank@caixabank.com"
    to_email = user.email
    subject = "Investment Sale Confirmation"

    body = f""" 

    Dear {user.name},
    
    You have successfully sold {units_sold:.2f} units of {asset_symbol}.

    Total Gain/Loss: ${gain_loss:.2f}

    Remaining holdings of GOLD: {current_holdings:.2f} units

    Summary of current assets:
    - GOLD: {current_holdings:.2f} units purchased at ${purchase_price}

    Account Balance: ${balance:.2f}
    Net Worth: ${balance + (current_holdings * purchase_price):.2f}

    Thank you for using our investment services.

    Best Regards,
    Investment Management Team
    """

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    smtp_server = "smtp"
    smtp_port = 1025

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.send_message(msg)


def deduct_subscription(app, user_id, amount, job_id):
    with app.app_context():
        user = User.query.get(user_id)

        if user and user.account.balance >= amount:
            # Deduct amount and create a transaction
            user.account.balance -= amount
            new_transaction = Transaction(
                user_id=user.id,
                amount=amount,
                transaction_type="SUBSCRIPTION",
                source_account_number=user.accountNumber,
                target_account_number="N/A",
            )
            db.session.add(new_transaction)
            db.session.commit()

        else:
            # Handle insufficient funds or user not found
            if user is None:
                print(f"User with id {user_id} not found.")
            elif user.account.balance < amount:
                print(
                    f"Insufficient funds for user with id {user_id}. Stopping subscription."
                )

            # Stop the subscription job
            scheduler.remove_job(job_id)


def schedule_subscription(app, user_id, amount, interval_seconds, job_id):
    scheduler.add_job(
        deduct_subscription,
        "interval",
        seconds=interval_seconds,
        args=[app, user_id, amount, job_id],
        id=job_id,
        next_run_time=datetime.now() + timedelta(seconds=interval_seconds),
    )
    print(f"Subscription job scheduled with ID: {job_id}")


def auto_invest(app, user_id):
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            return

        if not user.auto_invest_enabled:
            return

        # Fetch market prices
        market_prices = get_market_price()

        # Loop through user assets
        for asset in user.assets:
            current_price = market_prices.get(asset.asset_symbol)
            if not current_price:
                continue

            # Buy more if price drops to 80% of purchase price
            if current_price <= asset.purchase_price * 0.8:

                if user.account.balance >= user.account.balance * 0.1:
                    amount = user.account.balance * 0.1
                    purchase_price = current_price
                    units_purchased = amount / purchase_price

                    # Update balance and asset holdings
                    user.account.balance -= amount
                    asset.quantity += units_purchased

                    # Create an asset record
                    new_asset_purchase = Asset(
                        user_id=user.id,
                        asset_symbol=asset.asset_symbol,
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
                        target_account_number="N/A",
                    )

                    db.session.add(new_transaction)
                    db.session.add(new_asset_purchase)
                    db.session.commit()

                    # Query the total quantity of the given asset symbol
                    current_holdings = (
                        db.session.query(func.sum(Asset.quantity))
                        .filter_by(user_id=user.id, asset_symbol=asset.asset_symbol)
                        .scalar()
                    )

                    send_investment_confirmation_email(
                        user=user,
                        units_purchased=units_purchased,
                        asset_symbol=asset.asset_symbol,
                        amount=amount,
                        current_holdings=current_holdings,
                        purchase_price=purchase_price,
                        balance=user.account.balance,
                    )

            # Sell some if price rises to 120% of purchase price
            elif current_price >= asset.purchase_price * 1.2:

                if asset.quantity > 0:
                    quantity_to_sell = asset.quantity * 0.1
                    total_sale_value = quantity_to_sell * current_price
                    profitability = total_sale_value - (
                        quantity_to_sell * asset.purchase_price
                    )

                    # Update balance and asset holdings
                    user.account.balance += total_sale_value
                    asset.quantity -= quantity_to_sell

                    # Create a transaction record
                    new_transaction = Transaction(
                        user_id=user.id,
                        amount=total_sale_value,
                        transaction_type="ASSET_SALE",
                        source_account_number=user.accountNumber,
                        target_account_number="N/A",
                    )
                    db.session.add(new_transaction)
                    db.session.commit()

                    # Log profitability
                    print(f"Profitability for user {user.id}: ${profitability:.2f}")

                    new_profit = Profit(
                        user_id=user.id,
                        transaction_id=new_transaction.id,
                        profitability=profitability,
                    )

                    db.session.add(new_profit)
                    db.session.commit()

                    # Query the total quantity of the given asset symbol
                    current_holdings = (
                        db.session.query(func.sum(Asset.quantity))
                        .filter_by(user_id=user.id, asset_symbol=asset.asset_symbol)
                        .scalar()
                    )

                    send_investment_sale_confirmation_email(
                        user=user,
                        units_sold=quantity_to_sell,
                        asset_symbol=asset.asset_symbol,
                        gain_loss=profitability,
                        current_holdings=current_holdings,
                        purchase_price=asset.purchase_price,
                        balance=user.account.balance,
                    )


def schedule_auto_invest(app, user_id):
    scheduler.add_job(
        auto_invest,
        "interval",
        seconds=30,
        args=[app, user_id],
        next_run_time=datetime.now() + timedelta(seconds=30),
    )
