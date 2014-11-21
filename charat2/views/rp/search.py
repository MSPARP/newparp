import json

from flask import (
    abort, g, jsonify, make_response, redirect, render_template, request,
    url_for
)
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers import tags_to_set
from charat2.helpers.auth import log_in_required
from charat2.model import case_options, Character
from charat2.model.connections import use_db, db_commit, db_disconnect
from charat2.model.validators import color_validator


@use_db
@log_in_required
def search_get():
    return render_template("rp/search.html")


@use_db
@log_in_required
def search_post():
    # End the database session so the long poll doesn't hang onto it.
    # XXX don't create a database connection at all if they're already searching?
    db_commit()
    db_disconnect()
    pubsub = g.redis.pubsub()
    pubsub.subscribe("searcher:%s" % g.session_id)
    # XXX use a different id for each tab?
    g.redis.sadd("searchers", g.session_id)
    for msg in pubsub.listen():
        if msg["type"] == "message":
            # The pubsub channel sends us a JSON string, so we return that
            # instead of using jsonify.
            resp = make_response(msg["data"])
            resp.headers["Content-type"] = "application/json"
            return resp


@use_db
@log_in_required
def search_stop():
    g.redis.srem("searchers", g.session_id)
    # Kill the long poll request.
    g.redis.publish("searcher:%s" % g.session_id, "{\"status\":\"quit\"}")
    return "", 204


@use_db
@log_in_required
def search_save():

    # yeah this is just cut and pasted from chat_api.py
    # see also helpers/characters.py

    # Don't allow a blank name.
    if request.form["name"] == "":
        return redirect(url_for("home", search_error="empty_name"))

    # Validate color.
    # <input type="color"> always prefixes with a #.
    if request.form["color"][0] == "#":
        color = request.form["color"][1:]
    else:
        color = request.form["color"]
    if not color_validator.match(color):
        return redirect(url_for("home", search_error="bad_color"))
    g.user.color = color

    # Validate case.
    if request.form["case"] not in case_options:
        return redirect(url_for("home", search_error="bad_case"))
    g.user.case = request.form["case"]

    # There are length limits on the front end so just silently truncate these.
    g.user.name = request.form["name"][:50]
    g.user.alias = request.form["alias"][:15]
    g.user.quirk_prefix = request.form["quirk_prefix"][:50]
    g.user.quirk_suffix = request.form["quirk_suffix"][:50]

    # XXX PUT LENGTH LIMIT ON REPLACEMENTS?
    # Zip replacements.
    replacements = zip(
        request.form.getlist("quirk_from"),
        request.form.getlist("quirk_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    replacements = [_ for _ in replacements if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    g.user.replacements = json.dumps(replacements)

    # XXX PUT LENGTH LIMIT ON REGEXES?
    # Zip regexes.
    regexes = zip(
        request.form.getlist("regex_from"),
        request.form.getlist("regex_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    regexes = [_ for _ in regexes if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    g.user.regexes = json.dumps(regexes)

    return redirect(url_for("rp_search"))

