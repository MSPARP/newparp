from flask import g, render_template, url_for
from flask_mail import Message as EmailMessage
from uuid import uuid4

from newparp import mail


expiry_times = {
    "welcome": 86400,
    "verify": 86400,
    "reset": 600,
}

subjects = {
    "welcome": "Welcome to MSPARP",
    "verify": "Verify your e-mail address",
    "reset": "Reset your password",
}


def send_email(action, email_address):
    email_token = str(uuid4())
    g.redis.setex(
        ":".join([action, str(g.user.id), email_address]),
        expiry_times[action],
        email_token,
    )
    message = EmailMessage(
        subject=subjects[action],
        sender="admin@msparp.com",
        recipients=[email_address],
        body=render_template("email/%s_plain.html" % action, user=g.user, email_address=email_address, email_token=email_token),
        html=render_template("email/%s.html" % action, user=g.user, email_address=email_address, email_token=email_token),
    )
    mail.send(message)

