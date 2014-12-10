import json

from flask import (
    abort, g, jsonify, make_response, redirect, render_template, request,
    url_for
)
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4

from charat2.helpers import tags_to_set
from charat2.helpers.auth import log_in_required
from charat2.model import case_options, SearchCharacter, SearchCharacterChoice
from charat2.model.connections import use_db, db_commit, db_disconnect
from charat2.model.validators import color_validator


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

    all_character_ids = set(_[0] for _ in g.db.query(SearchCharacter.id).all())

    try:
        character_id = int(request.form["search_character_id"])
        if character_id not in all_character_ids:
            raise ValueError
        g.user.search_character_id = character_id
    except ValueError:
        g.user.search_character_id = 1

    # Picky checkboxes
    g.db.query(SearchCharacterChoice).filter(SearchCharacterChoice.user_id == g.user.id).delete()
    if "use_picky" in request.form:
        for key in request.form.keys():
            if not key.startswith("picky_"):
                continue
            try:
                character_id = int(key[6:])
            except:
                continue
            if not character_id in all_character_ids:
                continue
            g.db.add(SearchCharacterChoice(user_id=g.user.id, search_character_id=character_id))

    return redirect(url_for("rp_search"))


@use_db
@log_in_required
def search_get():
    return render_template("rp/search.html")


@use_db
@log_in_required
def search_post():
    searcher_id = str(uuid4())
    g.redis.set("searcher:%s:session_id" % searcher_id, g.session_id)
    g.redis.expire("searcher:%s:session_id" % searcher_id, 30)
    return jsonify({ "id": searcher_id })


def search_continue():

    searcher_id = request.form["id"][:36]
    cached_session_id = g.redis.get("searcher:%s:session_id" % searcher_id)

    # Send people back to /search if we don't have their data cached.
    if g.user_id is None or cached_session_id != g.session_id:
        abort(404)

    g.redis.expire("searcher:%s:session_id" % searcher_id, 30)

    pubsub = g.redis.pubsub()
    pubsub.subscribe("searcher:%s" % searcher_id)

    g.redis.sadd("searchers", searcher_id)

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
    searcher_id = request.form["id"][:36]
    g.redis.srem("searchers", searcher_id)
    # Kill the long poll request.
    g.redis.publish("searcher:%s" % searcher_id, "{\"status\":\"quit\"}")
    return "", 204

