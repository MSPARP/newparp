import paginate, re

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from charat2.helpers import alt_formats
from charat2.helpers.auth import permission_required
from charat2.model import AdminLogEntry, Message, SpamlessFilter
from charat2.model.connections import use_db


@alt_formats({"json"})
@use_db
@permission_required("spamless")
def home(fmt=None, page=1):

    messages = (
        g.db.query(Message)
        .filter(Message.spam_flag != None)
        .order_by(Message.id.desc())
        .options(
            joinedload(Message.chat),
            joinedload(Message.user),
            joinedload(Message.chat_user)
        )
        .offset((page - 1) * 50).limit(50).all()
    )

    if len(messages) == 0 and page != 1:
        abort(404)

    message_count = (
        g.db.query(func.count('*'))
        .select_from(Message)
        .filter(Message.spam_flag != None)
        .scalar()
    )

    if fmt == "json":
        return jsonify({
            "total": message_count,
            "messages": [_.to_dict(include_spam_flag=True) for _ in messages],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=message_count,
        url_maker=lambda page: url_for("spamless_home", page=page),
    )

    return render_template(
        "admin/spamless/home.html",
        messages=messages,
        paginator=paginator,
    )


def _banned_names(**kwargs):
    return render_template(
        "admin/spamless/banned_names.html",
        names=g.db.query(SpamlessFilter).filter(SpamlessFilter.type == "banned_names").all(),
        **kwargs
    )


@use_db
@permission_required("spamless")
def banned_names():
    return _banned_names()


@use_db
@permission_required("spamless")
def banned_names_post():
    # Validate the command is either adding or removing.
    if request.form["command"] not in ("add", "remove"):
        return _banned_names()

    # Consume and validate the name.
    name = request.form["name"].strip().lower()
    if not name:
        abort(400)

    try:
        re.compile(name)
    except re.error as e:
        return _banned_names(error=e.args[0])

    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="spamless:banned_names:%s" % request.form["command"],
        description=name,
    ))

    handle_command(request.form["command"], name, "banned_names")

    g.redis.publish("spamless:reload", 1)
    return redirect(url_for("spamless_banned_names"))


def _blacklist(**kwargs):
    return render_template(
        "admin/spamless/blacklist.html",
        phrases=g.db.query(SpamlessFilter).filter(SpamlessFilter.type == "blacklist").all(),
        **kwargs
    )


@use_db
@permission_required("spamless")
def blacklist():
    return _blacklist()


@use_db
@permission_required("spamless")
def blacklist_post():
    # Validate the command is either adding or removing.
    if request.form["command"] not in ("add", "remove"):
        return _blacklist()

    # Consume and validate the phrase.
    phrase = request.form["phrase"].strip().lower()
    score = request.form.get("score")
    if not phrase:
        abort(400)

    try:
        re.compile(phrase)
    except re.error as e:
        return _blacklist(error=e.args[0])

    handle_command(request.form["command"], phrase, "blacklist", score)

    if request.form["command"] == "add":
        log_message = "%s (%s)" % (phrase, score)
    else:
        log_message = phrase

    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="spamless:blacklist:%s" % request.form["command"],
        description=log_message,
    ))

    g.redis.publish("spamless:reload", 1)
    return redirect(url_for("spamless_blacklist"))


def _warnlist(**kwargs):
    return render_template(
        "admin/spamless/warnlist.html",
        phrases=g.db.query(SpamlessFilter).filter(SpamlessFilter.type == "warnlist").all(),
        **kwargs
    )


@use_db
@permission_required("spamless")
def warnlist():
    return _warnlist()


@use_db
@permission_required("spamless")
def warnlist_post():
    # Validate the command is either adding or removing.
    if request.form["command"] not in ("add", "remove"):
        return _warnlist()

    # Consume and validate the phrase.
    phrase = request.form["phrase"].strip().lower()
    if not phrase:
        abort(400)

    try:
        re.compile(phrase)
    except re.error as e:
        return _warnlist(error=e.args[0])

    # Add the phrase
    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="spamless:warnlist:%s" % request.form["command"],
        description=phrase,
    ))

    handle_command(request.form["command"], phrase, "warnlist")

    # Send the reload command.
    g.redis.publish("spamless:reload", 1)

    return redirect(url_for("spamless_warnlist"))

# Helper functions
def handle_command(command, phrase, filtertype, points=0):
    try:
        points = int(points.strip())
    except ValueError:
        abort(400)
    except AttributeError:
        pass

    if command == "add":
        g.db.add(SpamlessFilter(
            type=filtertype,
            regex=phrase,
            points=points
        ))
    else:
        g.db.query(SpamlessFilter).filter(SpamlessFilter.type == filtertype).filter(SpamlessFilter.regex == phrase).delete()

    g.db.commit()

