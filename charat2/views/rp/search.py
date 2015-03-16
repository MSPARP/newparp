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
from charat2.helpers.characters import validate_character_form
from charat2.model import case_options, SearchCharacter, SearchCharacterChoice, User
from charat2.model.connections import use_db, db_commit, db_disconnect
from charat2.model.validators import color_validator


@use_db
@log_in_required
def search_save():

    new_details = validate_character_form(request.form)
    g.user.search_character_id = new_details["search_character_id"]
    g.user.name = new_details["name"]
    g.user.acronym = new_details["acronym"]
    g.user.color = new_details["color"]
    g.user.quirk_prefix = new_details["quirk_prefix"]
    g.user.quirk_suffix = new_details["quirk_suffix"]
    g.user.case = new_details["case"]
    g.user.replacements = new_details["replacements"]
    g.user.regexes = new_details["regexes"]

    if request.form["style"] in User.search_style.type.enums:
        g.user.search_style = request.form["style"]

    if request.form["level"] in User.search_level.type.enums:
        g.user.search_level = request.form["level"]

    all_character_ids = set(_[0] for _ in g.db.query(SearchCharacter.id).all())

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

    g.redis.set("searcher:%s:search_character_id" % searcher_id, g.user.search_character_id)
    g.redis.expire("searcher:%s:search_character_id" % searcher_id, 30)

    g.redis.hmset("searcher:%s:character" % searcher_id, {
        "name": g.user.name,
        "acronym": g.user.acronym,
        "color": g.user.color,
        "quirk_prefix": g.user.quirk_prefix,
        "quirk_suffix": g.user.quirk_suffix,
        "case": g.user.case,
        "replacements": g.user.replacements,
        "regexes": g.user.regexes,
    })
    g.redis.expire("searcher:%s:character" % searcher_id, 30)

    g.redis.hmset("searcher:%s:options" % searcher_id, {
        "style": g.user.search_style,
        "level": g.user.search_level,
    })
    g.redis.expire("searcher:%s:options" % searcher_id, 30)

    g.redis.delete("searcher:%s:choices" % searcher_id)
    choices = [_[0] for _ in g.db.query(
        SearchCharacterChoice.search_character_id,
    ).filter(
        SearchCharacterChoice.user_id == g.user.id,
    ).all()]
    if choices:
        g.redis.sadd("searcher:%s:choices" % searcher_id, *choices)
    g.redis.expire("searcher:%s:choices" % searcher_id, 30)

    return jsonify({ "id": searcher_id })


def search_continue():

    searcher_id = request.form["id"][:36]
    cached_session_id = g.redis.get("searcher:%s:session_id" % searcher_id)

    # Send people back to /search if we don't have their data cached.
    if g.user_id is None or cached_session_id != g.session_id:
        abort(404)

    g.redis.expire("searcher:%s:session_id" % searcher_id, 30)
    g.redis.expire("searcher:%s:search_character_id" % searcher_id, 30)
    g.redis.expire("searcher:%s:character" % searcher_id, 30)
    g.redis.expire("searcher:%s:options" % searcher_id, 30)
    g.redis.expire("searcher:%s:choices" % searcher_id, 30)

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

