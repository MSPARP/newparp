import os

from flask import Flask, redirect, send_from_directory

from charat2.model.connections import (
    db_commit,
    db_disconnect,
    redis_connect,
    redis_disconnect,
    set_cookie,
)
from charat2.views import root, account, rp, blog
from charat2.views.rp import chat, chat_api, chat_list, characters, search

from flask.ext.babel import Babel, gettext

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config["SERVER_NAME"] = os.environ["BASE_DOMAIN"]
app.debug=True
babel = Babel(app)
app.jinja_env.globals.update(gettext=gettext)

app.before_request(redis_connect)

app.after_request(set_cookie)
app.after_request(db_commit)

app.teardown_request(db_disconnect)
app.teardown_request(redis_disconnect)

# 1. Root domain (charat.net)

app.add_url_rule("/", "home", root.home, methods=("GET",))

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "img/favicons/root/favicon.ico", mimetype="image/vnd.microsoft.icon")

app.add_url_rule("/login", "login_get", account.login_get, methods=("GET",))
app.add_url_rule("/register", "register_get", account.register_get, methods=("GET",))
app.add_url_rule("/login", "login_post", account.login_post, methods=("POST",))
app.add_url_rule("/logout", "logout", account.logout)
app.add_url_rule("/register", "register", account.register, methods=("POST",))

# 2. RP subdomain (rp.charat.net)

app.add_url_rule("/", "rp_home", rp.home, subdomain="rp", methods=("GET",))

@app.route("/favicon.ico", subdomain="rp")
def rp_favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "img/favicons/rp/favicon.ico", mimetype="image/vnd.microsoft.icon")

# 2.1. Chats list

app.add_url_rule("/chats", "chat_list", chat_list.chat_list, subdomain="rp", methods=("GET",))
app.add_url_rule("/chats.<fmt>", "chat_list", chat_list.chat_list, subdomain="rp", methods=("GET",))

app.add_url_rule("/chats/<int:page>", "chat_list", chat_list.chat_list, subdomain="rp", methods=("GET",))
app.add_url_rule("/chats/<int:page>.<fmt>", "chat_list", chat_list.chat_list, subdomain="rp", methods=("GET",))

app.add_url_rule("/chats/<type>", "chat_list", chat_list.chat_list, subdomain="rp", methods=("GET",))
app.add_url_rule("/chats/<type>.<fmt>", "chat_list", chat_list.chat_list, subdomain="rp", methods=("GET",))

app.add_url_rule("/chats/<type>/<int:page>", "chat_list", chat_list.chat_list, subdomain="rp", methods=("GET",))
app.add_url_rule("/chats/<type>/<int:page>.<fmt>", "chat_list", chat_list.chat_list, subdomain="rp", methods=("GET",))

# 2.2. Character management

app.add_url_rule("/characters", "character_list", characters.character_list, subdomain="rp", methods=("GET",))
app.add_url_rule("/characters.<fmt>", "character_list", characters.character_list, subdomain="rp", methods=("GET",))

app.add_url_rule("/characters/new", "new_character", characters.new_character, subdomain="rp", methods=("POST",))

app.add_url_rule("/characters/<int:character_id>", "character", characters.character, subdomain="rp", methods=("GET",))
app.add_url_rule("/characters/<int:character_id>.<fmt>", "character", characters.character, subdomain="rp", methods=("GET",))
app.add_url_rule("/characters/<int:character_id>/save", "save_character", characters.save_character, subdomain="rp", methods=("POST",))
app.add_url_rule("/characters/<int:character_id>/delete", "delete_character_get", characters.delete_character_get, subdomain="rp", methods=("GET",))
app.add_url_rule("/characters/<int:character_id>/delete", "delete_character_post", characters.delete_character_post, subdomain="rp", methods=("POST",))
app.add_url_rule("/characters/<int:character_id>/set_default", "set_default_character", characters.set_default_character, subdomain="rp", methods=("POST",))

# 2.3. Creating chats

app.add_url_rule("/create_chat", "create_chat", chat.create_chat, subdomain="rp", methods=("POST",))

# 2.4. Searching

app.add_url_rule("/search", "rp_search", search.search_get, subdomain="rp", methods=("GET",))
app.add_url_rule("/search", "rp_search_post", search.search_post, subdomain="rp", methods=("POST",))
app.add_url_rule("/search/stop", "rp_search_stop", search.search_stop, subdomain="rp", methods=("POST",))

# 2.5. Rooms

app.add_url_rule("/rooms", "rp_rooms", rp.rooms, subdomain="rp", methods=("GET",))
app.add_url_rule("/rooms.<fmt>", "rp_rooms", rp.rooms, subdomain="rp", methods=("GET",))

# 2.6. Chats

app.add_url_rule("/<path:url>", "chat", chat.chat, subdomain="rp", methods=("GET",))
app.add_url_rule("/<path:url>.<fmt>", "chat", chat.chat, subdomain="rp", methods=("GET",))

# Push the previous rules to the bottom so it doesn't catch /chats.json, /rooms.json etc.
app.url_map._rules[-2].match_compare_key = lambda: (True, 2, [])
app.url_map._rules[-1].match_compare_key = lambda: (True, 1, [])

app.add_url_rule("/<path:url>/log", "log", chat.log, subdomain="rp", methods=("GET",))
app.add_url_rule("/<path:url>/log/<int:page>", "log", chat.log, subdomain="rp", methods=("GET",))

app.add_url_rule("/<path:url>/users", "chat_users", chat.users, subdomain="rp", methods=("GET",))

# 2.7. Chat API

app.add_url_rule("/chat_api/messages", "messages", chat_api.messages, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/meta", "meta", chat_api.meta, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/send", "send", chat_api.send, subdomain="rp", methods=("post",))
app.add_url_rule("/chat_api/set_state", "set_state", chat_api.set_state, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/set_group", "set_group", chat_api.set_group, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/user_action", "user_action", chat_api.user_action, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/set_flag", "set_flag", chat_api.set_flag, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/set_topic", "set_topic", chat_api.set_topic, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/save", "save", chat_api.save, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/save_from_character", "save_from_character", chat_api.save_from_character, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/ping", "ping", chat_api.ping, subdomain="rp", methods=("POST",))
app.add_url_rule("/chat_api/quit", "quit", chat_api.quit, subdomain="rp", methods=("POST",))

# 3. Blog subdomain (blog.charat.net)

app.add_url_rule("/", "blog_home", blog.home, subdomain="blog",methods=("GET",))

@app.route("/favicon.ico", subdomain="blog")
def blog_favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "img/favicons/blog/favicon.ico", mimetype="image/vnd.microsoft.icon")

app.add_url_rule("/post/<post_id>", "blog_post", blog.view_post, subdomain="blog", methods=("GET",))
app.add_url_rule("/post/<post_id>/<post_title>", "blog_post", blog.view_post, subdomain="blog", methods=("GET",))
app.add_url_rule("/feed.json", "blog_feed", blog.feed, subdomain="blog", methods=("GET",))

# XXX dear fucking lord we need traversal

