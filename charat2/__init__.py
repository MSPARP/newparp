import os

from flask import Flask

from charat2.model.connections import (
    db_commit,
    db_disconnect,
    redis_connect,
    redis_disconnect,
    set_cookie,
)
from charat2.views import root, account, rp
from charat2.views.rp import chat, chat_api

app = Flask(__name__)
app.config["SERVER_NAME"] = os.environ["BASE_DOMAIN"]

app.before_request(redis_connect)

app.after_request(set_cookie)
app.after_request(db_commit)

app.teardown_request(db_disconnect)
app.teardown_request(redis_disconnect)

# Root domain (charat.net)

app.add_url_rule("/", "home", root.home, methods=("GET",))

app.add_url_rule("/login", "log_in", account.log_in, methods=("POST",))
app.add_url_rule("/logout", "log_out", account.log_out, methods=("POST",))
app.add_url_rule("/register", "register", account.register, methods=("POST",))

# RP subdomain (rp.charat.net)

app.add_url_rule("/", "rp_home", rp.home, subdomain="rp", methods=("GET",))

app.add_url_rule("/rooms", "rooms", rp.rooms, subdomain="rp", methods=("GET",))

app.add_url_rule("/create_chat", "create_chat", chat.create_chat, subdomain="rp", methods=("POST",))
app.add_url_rule("/<url>", "chat", chat.chat, subdomain="rp", methods=("GET",))

app.add_url_rule("/chat_api/messages", "messages", chat_api.messages, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/send", "send", chat_api.send, subdomain="rp", methods=("post",))
app.add_url_rule("/chat_api/set_state", "set_state", chat_api.set_state, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/set_group", "set_group", chat_api.set_group, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/user_action", "user_action", chat_api.user_action, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/set_flag", "set_flag", chat_api.set_flag, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/set_topic", "set_topic", chat_api.set_topic, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/save", "save", chat_api.save, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/ping", "ping", chat_api.ping, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/quit", "quit", chat_api.quit, subdomain="rp", methods=("POST",))

