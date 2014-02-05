from flask import Flask

from charat2.auth import get_request_user, set_cookie
from charat2.model.connections import (
    db_connect,
    db_disconnect,
    redis_connect,
    redis_disconnect
)
from charat2.views import home
from charat2.views.account import log_in, log_out, register

app = Flask(__name__)

app.before_request(redis_connect)
app.before_request(db_connect)
app.before_request(get_request_user)

app.after_request(db_disconnect)
app.after_request(redis_disconnect)
app.after_request(set_cookie)

app.add_url_rule("/", "home", home)

app.add_url_rule("/log-in", "log_in", log_in, methods=("POST",))
app.add_url_rule("/log-out", "log_out", log_out, methods=("POST",))
app.add_url_rule("/register", "register", register, methods=("POST",))

