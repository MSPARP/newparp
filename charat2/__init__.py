import os

from flask import Flask, redirect, send_from_directory

from charat2.model.connections import (
    db_commit,
    db_disconnect,
    redis_connect,
    redis_disconnect,
    set_cookie,
)
from charat2.views import account, admin, rp
from charat2.views.rp import chat, chat_api, chat_list, characters, request_search, search, search_characters

from flask.ext.babel import Babel, gettext

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config["SERVER_NAME"] = os.environ["BASE_DOMAIN"]

# XXX REMEMBER TO REMOVE THIS BEFORE LAUNCH
app.debug = True

babel = Babel(app)
app.jinja_env.globals.update(gettext=gettext)

app.before_request(redis_connect)

app.after_request(set_cookie)
app.after_request(db_commit)

app.teardown_request(db_disconnect)
app.teardown_request(redis_disconnect)


def make_rules(subdomain, path, func, formats=False, paging=False):
    # Keep subdomain here for consistency with charat2's route names.
    name = (subdomain + "_" + func.__name__) if subdomain else func.__name__
    app.add_url_rule(path, name, func, methods=("GET",))
    if formats:
        app.add_url_rule(path + ".<fmt>", name, func, methods=("GET",))
    if paging:
        app.add_url_rule(path + "/<int:page>", name, func, methods=("GET",))
    if formats and paging:
        app.add_url_rule(path + "/<int:page>.<fmt>", name, func, methods=("GET",))


# 1. Home/account

app.add_url_rule("/", "home", rp.home, methods=("GET",))

app.add_url_rule("/search_characters", "rp_search_character_list", search_characters.search_character_list, methods=("GET",))
app.add_url_rule("/search_characters/<int:id>", "rp_search_character", search_characters.search_character, methods=("GET",))
app.add_url_rule("/search_characters/<int:id>.json", "rp_search_character_json", search_characters.search_character_json, methods=("GET",))

app.add_url_rule("/log_in", "log_in", account.log_in_get, methods=("GET",))
app.add_url_rule("/log_in", "log_in_post", account.log_in_post, methods=("POST",))
app.add_url_rule("/log_out", "log_out", account.log_out, methods=("POST",))
app.add_url_rule("/register", "register", account.register_get, methods=("GET",))
app.add_url_rule("/register", "register_post", account.register_post, methods=("POST",))

# 2. Chats list

make_rules("rp", "/chats", chat_list.chat_list, formats=True, paging=True)
make_rules("rp", "/chats/<type>", chat_list.chat_list, formats=True, paging=True)

# 3. Character management

make_rules("rp", "/characters", characters.character_list, formats=True)

app.add_url_rule("/characters/new", "rp_new_character", characters.new_character, methods=("POST",))

make_rules("rp", "/characters/<int:character_id>", characters.character, formats=True)

app.add_url_rule("/characters/<int:character_id>/save", "rp_save_character", characters.save_character, methods=("POST",))
app.add_url_rule("/characters/<int:character_id>/delete", "rp_delete_character_get", characters.delete_character_get, methods=("GET",))
app.add_url_rule("/characters/<int:character_id>/delete", "rp_delete_character_post", characters.delete_character_post, methods=("POST",))
app.add_url_rule("/characters/<int:character_id>/set_default", "rp_set_default_character", characters.set_default_character, methods=("POST",))

# 4. Creating chats

app.add_url_rule("/create_chat", "rp_create_chat", chat.create_chat, methods=("POST",))

# 5. Searching

app.add_url_rule("/search/save", "rp_search_save", search.search_save, methods=("POST",))
app.add_url_rule("/search", "rp_search", search.search_get, methods=("GET",))
app.add_url_rule("/search", "rp_search_post", search.search_post, methods=("POST",))
app.add_url_rule("/search/continue", "rp_search_continue", search.search_continue, methods=("POST",))
app.add_url_rule("/search/stop", "rp_search_stop", search.search_stop, methods=("POST",))

# 6. Request searching

#make_rules("rp", "/requests", request_search.request_list, formats=True, paging=True)
#make_rules("rp", "/requests/yours", request_search.your_request_list, formats=True, paging=True)
#make_rules("rp", "/requests/<tag_type>:<name>", request_search.tagged_request_list, formats=True, paging=True)

#app.add_url_rule("/requests/new", "rp_new_request_get", request_search.new_request_get, methods=("GET",))
#app.add_url_rule("/requests/new", "rp_new_request_post", request_search.new_request_post, methods=("POST",))

#app.add_url_rule("/requests/answer/<int:request_id>", "rp_answer_request", request_search.answer_request, methods=("POST",))

#app.add_url_rule("/requests/edit/<int:request_id>", "rp_edit_request_get", request_search.edit_request_get, methods=("GET",))
#app.add_url_rule("/requests/edit/<int:request_id>", "rp_edit_request_post", request_search.edit_request_post, methods=("POST",))

#app.add_url_rule("/requests/delete/<int:request_id>", "rp_delete_request_get", request_search.delete_request_get, methods=("GET",))
#app.add_url_rule("/requests/delete/<int:request_id>", "rp_delete_request_post", request_search.delete_request_post, methods=("POST",))

# 7. Rooms

make_rules("rp", "/groups", rp.groups, formats=True)

# 8. Chats

make_rules("rp", "/<path:url>", chat.chat, formats=True)

# Push the previous rules to the bottom so it doesn't catch /chats.json, /groups.json etc.
app.url_map._rules[-2].match_compare_key = lambda: (True, 2, [])
app.url_map._rules[-1].match_compare_key = lambda: (True, 1, [])

make_rules("rp", "/<path:url>/log", chat.log, formats=True, paging=True)

make_rules("rp", "/<path:url>/users", chat.users, formats=True)

app.add_url_rule("/<path:url>/subscribe", "rp_chat_subscribe", chat.subscribe, methods=("POST",))
app.add_url_rule("/<path:url>/unsubscribe", "rp_chat_unsubscribe", chat.unsubscribe, methods=("POST",))

# 9. Chat API

app.add_url_rule("/chat_api/messages", "messages", chat_api.messages, methods=("POST",))
app.add_url_rule("/chat_api/send", "send", chat_api.send, methods=("POST",))
app.add_url_rule("/chat_api/set_state", "set_state", chat_api.set_state, methods=("POST",))
app.add_url_rule("/chat_api/set_group", "set_group", chat_api.set_group, methods=("POST",))
app.add_url_rule("/chat_api/user_action", "user_action", chat_api.user_action, methods=("POST",))
app.add_url_rule("/chat_api/set_flag", "set_flag", chat_api.set_flag, methods=("POST",))
app.add_url_rule("/chat_api/set_topic", "set_topic", chat_api.set_topic, methods=("POST",))
app.add_url_rule("/chat_api/set_info", "set_info", chat_api.set_info, methods=("POST",))
app.add_url_rule("/chat_api/save", "save", chat_api.save, methods=("POST",))
app.add_url_rule("/chat_api/save_from_character", "save_from_character", chat_api.save_from_character, methods=("POST",))
app.add_url_rule("/chat_api/save_variables", "save_variables", chat_api.save_variables, methods=("POST",))
app.add_url_rule("/chat_api/ping", "ping", chat_api.ping, methods=("POST",))
app.add_url_rule("/chat_api/quit", "quit", chat_api.quit, methods=("POST",))

# 10. Admin

app.add_url_rule("/admin/announcements", "admin_announcements", admin.announcements_get, methods=("GET",))
app.add_url_rule("/admin/announcements", "admin_announcements_post", admin.announcements_post, methods=("POST",))

# XXX dear fucking lord we need traversal

