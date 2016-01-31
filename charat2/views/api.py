from flask import g, request, jsonify
from sqlalchemy import func

from charat2.model import PushToken
from charat2.model.connections import use_db
from charat2.helpers.auth import log_in_required
from charat2.model.validators import valid_push_endpoint

@use_db
@log_in_required
def notifications():
    if "latest" in request.form:
        try:
            latest = int(request.form["latest"])
        except (TypeError, ValueError):
            latest = 0

        g.redis.setex("user:%s:notifications:latest" % (g.user_id), latest, 60)

        return "", 204
    elif "endpoint" in request.form:
        endpoint = request.form["endpoint"].strip()

        if valid_push_endpoint(endpoint):
            if g.db.query(PushToken).filter(PushToken.creator_id == g.user_id).filter(func.lower(PushToken.endpoint) == endpoint.lower()).scalar():
                return "", 204

            g.db.add(PushToken(
                creator_id=g.user_id,
                endpoint=endpoint
            ))

            return "", 204
    elif "revoke" in request.form:
        g.db.query(PushToken).filter(PushToken.creator_id == g.user_id).filter(func.lower(PushToken.endpoint) == endpoint.lower()).delete()
        return "", 204

    return jsonify({
        "notifications": g.redis.lrange("user:%s:notifications" % (g.user_id), 0, -1),
        "latest": g.redis.get("user:%s:notifications:latest" % (g.user_id))
    })

@use_db
@log_in_required
def token():
    return jsonify({"token": g.csrf_token})
