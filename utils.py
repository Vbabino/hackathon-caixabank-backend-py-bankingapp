from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from models import *
from sqlalchemy import exists
import smtplib

def is_token_revoked(jti):
    token_revoked = db.session.query(exists().where(RevokedToken.token == jti)).scalar()
    return token_revoked

def send_email(to_email, otp):
    from_email = "CaixaBank@caixabank.com"
    subject = "Your OTP Code"
    body = f"OTP: {otp}"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, 'plain'))

    smtp_server = "smtp"
    smtp_port = 1025

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.send_message(msg)
