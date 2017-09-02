import os
import logging

from flask import Flask, abort, redirect, request, send_from_directory
from flask_mail import Mail
from werkzeug.routing import BaseConverter

from newparp.helpers import check_csrf_token
from newparp.model.connections import (
    db_commit,
    db_disconnect,
    redis_connect,
    redis_disconnect,
    set_cookie,
)


app = Flask(__name__)
app.url_map.strict_slashes = False


# Config

app.config["SERVER_NAME"] = os.environ["BASE_DOMAIN"]
app.config["SENTRY_PRIVATE_DSN"] = os.environ.get("SENTRY_PRIVATE_DSN", None)
app.config["SENTRY_PUBLIC_DSN"] = os.environ.get("SENTRY_PUBLIC_DSN", None)
app.config['PROPAGATE_EXCEPTIONS'] = True

if app.config["SENTRY_PRIVATE_DSN"]:  # pragma: no cover
    from raven.contrib.flask import Sentry
    app.config["SENTRY_INCLUDE_PATHS"] = ["newparp"]
    sentry = Sentry(app,
        dsn=app.config["SENTRY_PRIVATE_DSN"],
        logging=True,
        level=logging.ERROR,
    )
    logging.getLogger("sentry.errors.uncaught").setLevel(logging.CRITICAL)
else:
    sentry = None

app.before_request(redis_connect)

app.before_request(check_csrf_token)

app.after_request(set_cookie)
app.after_request(db_commit)

app.teardown_request(db_disconnect)
app.teardown_request(redis_disconnect)


app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "localhost")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 25))
app.config["MAIL_USE_TLS"] = "MAIL_USE_TLS" in os.environ
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_SUPPRESS_SEND"] = app.testing or bool(os.environ.get("NOMAIL"))
mail = Mail(app)


# Views/routes

from newparp import views
from newparp.views import (
    account, admin, characters, chat, chat_api, chat_list, errors, guides,
    search, search_characters, settings,
)
from newparp.views.admin import spamless, spamless2


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


def make_rules(subdomain, path, func, formats=False, paging=False):
    # Keep subdomain here for consistency with charat2's route names.
    # TODO remove the subdomain stuff
    name = (subdomain + "_" + func.__name__) if subdomain else func.__name__
    app.add_url_rule(path, name, func, methods=("GET",))
    if formats:
        app.add_url_rule(path + ".<fmt>", name, func, methods=("GET",))
    if paging:
        app.add_url_rule(path + "/<int:page>", name, func, methods=("GET",))
    if formats and paging:
        app.add_url_rule(path + "/<int:page>.<fmt>", name, func, methods=("GET",))


# 1. Home/account

app.add_url_rule("/health", "health", views.health, methods=("GET",))

app.add_url_rule("/", "home", views.home, methods=("GET",))

make_rules("unread", "/unread", views.unread, formats=True)

app.add_url_rule("/log_in", "log_in", account.log_in_get, methods=("GET",))
app.add_url_rule("/log_in", "log_in_post", account.log_in_post, methods=("POST",))
app.add_url_rule("/log_in.<fmt>", "log_in_post", account.log_in_post, methods=("POST",))
# Fake rule for GET, because if we only accept POST then the chat creation check
# doesn't find it.
app.add_url_rule("/log_out", "log_out_404", lambda: abort(404), methods=("GET",))
app.add_url_rule("/log_out", "log_out", account.log_out, methods=("POST",))
app.add_url_rule("/register", "register", account.register_get, methods=("GET",))
app.add_url_rule("/register", "register_post", account.register_post, methods=("POST",))

app.add_url_rule("/reset_password", "reset_password", account.reset_password_get, methods=("GET",))
app.add_url_rule("/reset_password", "reset_password_post", account.reset_password_post, methods=("POST",))
app.add_url_rule("/forgot_password", "forgot_password", account.forgot_password_get, methods=("GET",))
app.add_url_rule("/forgot_password", "forgot_password_post", account.forgot_password_post, methods=("POST",))

app.add_url_rule("/settings", "settings", settings.home_get, methods=("GET",))
app.add_url_rule("/settings", "settings_post", settings.home_post, methods=("POST",))
app.add_url_rule("/settings/timezone", "settings_timezone", settings.timezone, methods=("POST",))
app.add_url_rule("/settings/theme", "settings_theme", settings.theme, methods=("POST",))
app.add_url_rule("/settings/pm_age_restriction", "settings_pm_age_restriction", settings.pm_age_restriction, methods=("POST",))
app.add_url_rule("/settings/date_of_birth", "settings_date_of_birth", settings.date_of_birth, methods=("POST",))
app.add_url_rule("/settings/log_in_details", "settings_log_in_details", settings.log_in_details, methods=("GET",))
app.add_url_rule("/settings/change_email", "settings_change_email", settings.change_email, methods=("POST",))
app.add_url_rule("/settings/verify_email", "settings_verify_email", settings.verify_email, methods=("GET",))
app.add_url_rule("/settings/change_password", "settings_change_password", settings.change_password, methods=("POST",))
make_rules("settings", "/settings/blocks", settings.blocks, formats=True)
app.add_url_rule("/settings/unblock", "settings_unblock", settings.unblock, methods=("POST",))

# 2. Chats list

make_rules("rp", "/chats", chat_list.chat_list, formats=True, paging=True)
make_rules("rp", "/chats/<type>", chat_list.chat_list, formats=True, paging=True)

# 3. Character management

make_rules("rp", "/characters", characters.character_list, formats=True)

app.add_url_rule("/characters/new", "rp_new_character_get", characters.new_character_get, methods=("GET",))
app.add_url_rule("/characters/new", "rp_new_character_post", characters.new_character_post, methods=("POST",))

make_rules("rp", "/characters/<int:character_id>", characters.character, formats=True)

app.add_url_rule("/characters/<int:character_id>/save", "rp_save_character", characters.save_character, methods=("POST",))
app.add_url_rule("/characters/<int:character_id>/delete", "rp_delete_character_get", characters.delete_character_get, methods=("GET",))
app.add_url_rule("/characters/<int:character_id>/delete", "rp_delete_character_post", characters.delete_character_post, methods=("POST",))
app.add_url_rule("/characters/<int:character_id>/set_default", "rp_set_default_character", characters.set_default_character, methods=("POST",))

# 4. Creating chats

app.add_url_rule("/create_chat", "rp_create_chat", chat.create_chat, methods=("POST",))

# 5. Searching

app.add_url_rule("/search_characters", "rp_search_character_list", search_characters.search_character_list, methods=("GET",))
app.add_url_rule("/search_characters/new_fandom", "rp_new_fandom_post", search_characters.new_fandom_post, methods=("POST",))
app.add_url_rule("/search_characters/new_group", "rp_new_search_character_group_post", search_characters.new_search_character_group_post, methods=("POST",))
app.add_url_rule("/search_characters/new", "rp_new_search_character_get", search_characters.new_search_character_get, methods=("GET",))
app.add_url_rule("/search_characters/new", "rp_new_search_character_post", search_characters.new_search_character_post, methods=("POST",))
app.add_url_rule("/search_characters/<int:id>", "rp_search_character", search_characters.search_character, methods=("GET",))
app.add_url_rule("/search_characters/<int:id>.json", "rp_search_character_json", search_characters.search_character_json, methods=("GET",))
app.add_url_rule("/search_characters/<int:id>/save", "rp_save_search_character", search_characters.save_search_character, methods=("POST",))
app.add_url_rule("/search_characters/<int:id>/delete", "rp_delete_search_character_get", search_characters.delete_search_character_get, methods=("GET",))
app.add_url_rule("/search_characters/<int:id>/delete", "rp_delete_search_character_post", search_characters.delete_search_character_post, methods=("POST",))

app.add_url_rule("/search/save", "rp_search_save", search.search_save, methods=("POST",))
app.add_url_rule("/search", "rp_search", search.search_get, methods=("GET",))
app.add_url_rule("/search", "rp_search_post", search.search_post, methods=("POST",))

# 6. Groups

make_rules("rp", "/groups", views.groups, formats=True)

# 7. Chats

make_rules("rp", "/<path:url>", chat.chat, formats=True)

# Push the previous rules to the bottom so it doesn't catch /chats.json, /groups.json etc.
app.url_map._rules[-2].match_compare_key = lambda: (True, 2, [])
app.url_map._rules[-1].match_compare_key = lambda: (True, 1, [])

make_rules("rp", "/<path:url>/log", chat.log, formats=True)
make_rules("rp", "/<path:url>/log/<int:page>", chat.log_page, formats=True)
make_rules("rp", "/<path:url>/log/<regex(\"20[0-9]{2}\"):year>-<regex(\"0[1-9]|1[0-2]\"):month>-<regex(\"0[1-9]|[1-2][0-9]|3[0-1]\"):day>", chat.log_day, formats=True)

make_rules("rp", "/<path:url>/users", chat.users, formats=True, paging=True)
app.add_url_rule("/<path:url>/users/reset_regexes", "rp_chat_reset_regexes", chat.reset_regexes, methods=("POST",))
make_rules("rp", "/<path:url>/invites", chat.invites, formats=True, paging=True)

app.add_url_rule("/<path:url>/uninvite", "rp_chat_uninvite", chat.uninvite, methods=("POST",))
app.add_url_rule("/<path:url>/invite", "rp_chat_invite", chat.invite, methods=("POST",))
app.add_url_rule("/<path:url>/unban", "rp_chat_unban", chat.unban, methods=("POST",))
app.add_url_rule("/<path:url>/subscribe", "rp_chat_subscribe", chat.subscribe, methods=("POST",))
app.add_url_rule("/<path:url>/unsubscribe", "rp_chat_unsubscribe", chat.unsubscribe, methods=("POST",))

app.add_url_rule("/redirect", "redirect", views.redirect_view, methods=("GET",))

# 8. Chat API

app.add_url_rule("/chat_api/send", "send", chat_api.send, methods=("POST",))
app.add_url_rule("/chat_api/draft", "draft", chat_api.draft, methods=("POST",))
app.add_url_rule("/chat_api/block", "block", chat_api.block, methods=("POST",))
app.add_url_rule("/chat_api/set_state", "set_state", chat_api.set_state, methods=("POST",))
app.add_url_rule("/chat_api/set_group", "set_group", chat_api.set_group, methods=("POST",))
app.add_url_rule("/chat_api/user_action", "user_action", chat_api.user_action, methods=("POST",))
app.add_url_rule("/chat_api/set_flag", "set_flag", chat_api.set_flag, methods=("POST",))
app.add_url_rule("/chat_api/set_topic", "set_topic", chat_api.set_topic, methods=("POST",))
app.add_url_rule("/chat_api/set_info", "set_info", chat_api.set_info, methods=("POST",))
app.add_url_rule("/chat_api/save", "save", chat_api.save, methods=("POST",))
app.add_url_rule("/chat_api/save_from_character", "save_from_character", chat_api.save_from_character, methods=("POST",))
app.add_url_rule("/chat_api/save_variables", "save_variables", chat_api.save_variables, methods=("POST",))
app.add_url_rule("/chat_api/request_username", "request_username", chat_api.request_username, methods=("POST",))
app.add_url_rule("/chat_api/exchange_usernames", "exchange_usernames", chat_api.exchange_usernames, methods=("POST",))
app.add_url_rule("/chat_api/look_up_user", "look_up_user", chat_api.look_up_user, methods=("POST",))

# 9. Admin

app.add_url_rule("/admin", "admin_home", admin.home, methods=("GET",))

app.add_url_rule("/admin/announcements", "admin_announcements", admin.announcements_get, methods=("GET",))
app.add_url_rule("/admin/announcements", "admin_announcements_post", admin.announcements_post, methods=("POST",))

app.add_url_rule("/admin/broadcast", "admin_broadcast", admin.broadcast_get, methods=("GET",))
app.add_url_rule("/admin/broadcast", "admin_broadcast_post", admin.broadcast_post, methods=("POST",))

make_rules("admin", "/admin/users", admin.user_list, formats=True)
make_rules("admin", "/admin/users/<username>", admin.user, formats=True)
app.add_url_rule("/admin/users/<username>/set_group", "admin_user_set_group", admin.user_set_group, methods=("POST",))
app.add_url_rule("/admin/users/<username>/set_admin_tier", "admin_user_set_admin_tier", admin.user_set_admin_tier, methods=("POST",))
app.add_url_rule("/admin/users/<username>/reset_password", "admin_user_reset_password", admin.user_reset_password_get, methods=("GET",))
app.add_url_rule("/admin/users/<username>/reset_password", "admin_user_reset_password_post", admin.user_reset_password_post, methods=("POST",))
app.add_url_rule("/admin/users/<username>/notes", "admin_user_notes_post", admin.user_notes_post, methods=("POST",))

make_rules("admin", "/admin/blocks", admin.block_list, formats=True, paging=True)

make_rules("admin", "/admin/permissions", admin.permissions, formats=True)
app.add_url_rule("/admin/permissions/new", "admin_new_admin_tier", admin.new_admin_tier, methods=("POST",))
make_rules("admin", "/admin/permissions/<admin_tier_id>", admin.admin_tier_get, formats=True)
app.add_url_rule("/admin/permissions/<admin_tier_id>", "admin_admin_tier_post", admin.admin_tier_post, methods=("POST",))
app.add_url_rule("/admin/permissions/<admin_tier_id>/add_user", "admin_admin_tier_add_user", admin.admin_tier_add_user, methods=("POST",))

make_rules("admin", "/admin/groups", admin.groups, formats=True, paging=True)

make_rules("admin", "/admin/log", admin.log, formats=True, paging=True)

make_rules("spamless", "/admin/spamless", spamless.home, formats=True)
app.add_url_rule("/admin/spamless/banned_names", "spamless_banned_names", spamless.banned_names)
app.add_url_rule("/admin/spamless/banned_names", "spamless_banned_names_post", spamless.banned_names_post, methods=("POST",))
app.add_url_rule("/admin/spamless/blacklist", "spamless_blacklist", spamless.blacklist)
app.add_url_rule("/admin/spamless/blacklist", "spamless_blacklist_post", spamless.blacklist_post, methods=("POST",))
app.add_url_rule("/admin/spamless/warnlist", "spamless_warnlist", spamless.warnlist)
app.add_url_rule("/admin/spamless/warnlist", "spamless_warnlist_post", spamless.warnlist_post, methods=("POST",))

make_rules("spamless2", "/admin/spamless2", spamless2.home, formats=True, paging=True)

make_rules("admin", "/admin/ip_bans", admin.ip_bans, formats=True, paging=True)
app.add_url_rule("/admin/ip_bans/new", "admin_new_ip_ban", admin.new_ip_ban, methods=("POST",))
app.add_url_rule("/admin/ip_bans/delete", "admin_delete_ip_ban", admin.delete_ip_ban, methods=("POST",))

make_rules("admin", "/admin/email_bans", admin.email_bans, formats=True)
app.add_url_rule("/admin/email_bans/new", "admin_new_email_ban", admin.new_email_ban, methods=("POST",))
app.add_url_rule("/admin/email_bans/delete", "admin_delete_email_ban", admin.delete_email_ban, methods=("POST",))

app.add_url_rule("/admin/worker_status", "admin_worker_status", admin.worker_status, methods=("GET",))

# 10. Guides

app.add_url_rule("/userguide", "guides_user_guide", guides.user_guide, methods=("GET",))
app.add_url_rule("/bbcodeguide", "guides_bbcode_guide", guides.bbcode_guide, methods=("GET",))

# 11. Error handlers

app.register_error_handler(403, errors.error_403)
app.register_error_handler(404, errors.error_404)
app.register_error_handler(500, errors.error_500)

if not app.debug and not app.testing:
    app.register_error_handler(Exception, errors.error_500)

# 12. Log cabin

app.add_url_rule("/api/users.json", "api_users", views.api_users, methods=("GET",))

# XXX dear fucking lord we need traversal

