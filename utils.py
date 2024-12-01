from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from models import *
from sqlalchemy import exists
import smtplib
import requests


def is_token_revoked(jti):
    token_revoked = db.session.query(exists().where(RevokedToken.token == jti)).scalar()
    return token_revoked


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
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    smtp_server = 'smtp'
    smtp_port = 1025

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.send_message(msg)
