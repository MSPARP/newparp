import paginate

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from charat2.helpers import alt_formats
from charat2.helpers.auth import permission_required
from charat2.model import AdminLogEntry, Message
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


@use_db
@permission_required("spamless")
def banned_names():
    return render_template(
        "admin/spamless/banned_names.html",
        names=sorted(list(g.redis.smembers("spamless:banned_names"))),
    )


@use_db
@permission_required("spamless")
def banned_names_post():
    command_functions = {"add": g.redis.sadd, "remove": g.redis.srem}
    try:
        command = command_functions[request.form["command"]]
    except KeyError:
        abort(400)
    name = request.form["name"].strip().lower()
    if not name:
        abort(400)
    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="spamless:banned_names:%s" % request.form["command"],
        description=name,
    ))
    command("spamless:banned_names", name)
    g.redis.publish("spamless:reload", 1)
    return redirect(url_for("spamless_banned_names"))


@use_db
@permission_required("spamless")
def blacklist():
    return render_template(
        "admin/spamless/blacklist.html",
        phrases=sorted(list(
            (phrase, int(score)) for phrase, score in
            g.redis.zrange("spamless:blacklist", 0, -1, withscores=True)
        )),
    )


@use_db
@permission_required("spamless")
def blacklist_post():
    phrase = request.form["phrase"].strip().lower()
    if not phrase:
        abort(400)
    if request.form["command"] == "add":
        try:
            score = int(request.form["score"].strip())
        except ValueError:
            abort(400)
        g.redis.zadd("spamless:blacklist", score, phrase)
        log_message = "%s (%s)" % (phrase, score)
    elif request.form["command"] == "remove":
        g.redis.zrem("spamless:blacklist", phrase)
        log_message = phrase
    else:
        abort(400)
    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="spamless:blacklist:%s" % request.form["command"],
        description=log_message,
    ))
    g.redis.publish("spamless:reload", 1)
    return redirect(url_for("spamless_blacklist"))


@use_db
@permission_required("spamless")
def warnlist():
    return render_template(
        "admin/spamless/warnlist.html",
        phrases=sorted(list(g.redis.smembers("spamless:warnlist"))),
    )


@use_db
@permission_required("spamless")
def warnlist_post():
    command_functions = {"add": g.redis.sadd, "remove": g.redis.srem}
    try:
        command = command_functions[request.form["command"]]
    except KeyError:
        abort(400)
    phrase = request.form["phrase"].strip().lower()
    if not phrase:
        abort(400)
    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="spamless:warnlist:%s" % request.form["command"],
        description=phrase,
    ))
    command("spamless:warnlist", phrase)
    g.redis.publish("spamless:reload", 1)
    return redirect(url_for("spamless_warnlist"))

