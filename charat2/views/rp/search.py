from flask import (
    abort, g, jsonify, make_response, redirect, render_template, request,
    url_for
)

from charat2.helpers.auth import login_required
from charat2.model import UserCharacter
from charat2.model.connections import use_db, db_commit, db_disconnect


@use_db
@login_required
def search_get():

    characters = g.db.query(UserCharacter).filter(
        UserCharacter.user_id == g.user.id,
    ).order_by(UserCharacter.title, UserCharacter.id).all()

    return render_template(
        "rp/search.html",
        characters=characters,
    )


@use_db
@login_required
def search_post():

    db_commit()
    db_disconnect()

    # XXX use a different id for each tab?
    g.redis.sadd("searchers", g.session_id)

    pubsub = g.redis.pubsub()
    pubsub.subscribe("searcher:%s" % g.session_id)

    for msg in pubsub.listen():
        if msg["type"]=="message":
            # The pubsub channel sends us a JSON string, so we return that
            # instead of using jsonify.
            resp = make_response(msg["data"])
            resp.headers["Content-type"] = "application/json"
            return resp


@use_db
@login_required
def search_stop():

    g.redis.srem("searchers", g.session_id)

    # Kill the long poll request.
    g.redis.publish("searcher:%s" % g.session_id, "{\"status\":\"quit\"}")

    return "", 204

