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

    # End the database session so the long poll doesn't hang onto it.
    db_commit()
    db_disconnect()

    # This is just making sure it's a number, the actual validation happens
    # after the person is matched to save on database queries.
    try:
        character_id = int(request.form["character_id"])
        g.redis.set("session:%s:character_id" % g.session_id, character_id)
        g.redis.expire("session:%s:character_id" % g.session_id, 30)
    except:
        g.redis.delete("session:%s:character_id" % g.session_id)

    tags = set()
    # Tags are a single string separated by commas, so we split and trim it
    # here.
    # XXX use several fields like we do for replacements?
    for tag in request.form["tags"].split(","):
        tag = tag.strip()
        if tag == "":
            continue
        tags.add(tag.lower())
    g.redis.delete("session:%s:tags" % g.session_id)
    if len(tags) > 0:
        g.redis.sadd("session:%s:tags" % g.session_id, *tags)
        g.redis.expire("session:%s:tags" % g.session_id, 30)

    pubsub = g.redis.pubsub()
    pubsub.subscribe("searcher:%s" % g.session_id)

    # XXX use a different id for each tab?
    g.redis.sadd("searchers", g.session_id)

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

