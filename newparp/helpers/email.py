from flask import g, url_for
from flask_mail import Message as EmailMessage
from uuid import uuid4

from newparp import mail


def send_email(action, email_address):
    email_token = str(uuid4())
    g.redis.setex(":".join([action, str(g.user.id), email_address]), 86400 if action == "verify" else 600, email_token)

    message = EmailMessage(
        subject="Verify your email address",
        sender="admin@msparp.com",
        recipients=[email_address],
        body=url_for("settings_verify_email", user_id=g.user.id, email_address=email_address, token=email_token, _external=True),
    )
    mail.send(message)

