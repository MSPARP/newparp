from flask import abort, g, jsonify, make_response, redirect, render_template, request, url_for
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4

from charat2.helpers.auth import log_in_required
from charat2.model import Character, SearchCharacter
from charat2.model.connections import use_db


@use_db
@log_in_required
def roulette_save():
    try:
        form_id = int(request.form["id"][2:])
    except ValueError:
        abort(404)
    # Character
    if request.form["id"][0] == "c":
        try:
            character = g.db.query(Character).filter(
                Character.id == form_id,
            ).one()
        except NoResultFound:
            abort(404)
        g.user.roulette_search_character_id = 1
        g.user.roulette_character = character
    # Search character
    elif request.form["id"][0] == "s":
        try:
            search_character = g.db.query(SearchCharacter).filter(
                SearchCharacter.id == form_id,
            ).one()
        except NoResultFound:
            abort(404)
        g.user.roulette_search_character = search_character
        g.user.roulette_character = None
    else:
        abort(400)
    return redirect(url_for("rp_roulette"))


@use_db
@log_in_required
def roulette_get():
    return render_template("rp/roulette.html")


@use_db
@log_in_required
def roulette_post():
    searcher_id = str(uuid4())
    g.redis.set("roulette:%s:session_id" % searcher_id, g.session_id)
    g.redis.set("roulette:%s:search_character_id" % searcher_id, g.user.roulette_search_character_id)
    if g.user.roulette_character_id is not None:
        g.redis.set("roulette:%s:character_id" % searcher_id, g.user.roulette_character_id)
    g.redis.expire("roulette:%s:session_id" % searcher_id, 30)
    g.redis.expire("roulette:%s:search_character_id" % searcher_id, 30)
    g.redis.expire("roulette:%s:character_id" % searcher_id, 30)
    return jsonify({ "id": searcher_id })


def roulette_continue():
    searcher_id = request.form["id"][:36]
    cached_session_id = g.redis.get("roulette:%s:session_id" % searcher_id)
    # Send people back to /roulette if we don't have their data cached.
    if g.user_id is None or cached_session_id != g.session_id:
        abort(404)
    g.redis.expire("roulette:%s:session_id" % searcher_id, 30)
    g.redis.expire("roulette:%s:search_character_id" % searcher_id, 30)
    g.redis.expire("roulette:%s:character_id" % searcher_id, 30)
    pubsub = g.redis.pubsub()
    pubsub.subscribe("roulette:%s" % searcher_id)
    g.redis.sadd("roulette_searchers", searcher_id)
    for msg in pubsub.listen():
        if msg["type"] == "message":
            # The pubsub channel sends us a JSON string, so we return that
            # instead of using jsonify.
            resp = make_response(msg["data"])
            resp.headers["Content-type"] = "application/json"
            return resp


@use_db
@log_in_required
def roulette_stop():
    searcher_id = request.form["id"][:36]
    g.redis.srem("roulette_searchers", searcher_id)
    # Kill the long poll request.
    g.redis.publish("roulette:%s" % searcher_id, "{\"status\":\"quit\"}")
    return "", 204


