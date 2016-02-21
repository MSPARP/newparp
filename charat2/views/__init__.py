import os

from flask import g, current_app, jsonify

from charat2.model import SearchCharacter
from charat2.model.connections import use_db

@use_db
def health():
    g.redis.set("health", 1)
    g.db.query(SearchCharacter).first()
    return "ok"

def manifest():
    return jsonify({
        "name": "MSPARP",
        "short_name": "MSPARP",
        "icons": [
            {
                "src": "/static/img/spinner-big.png",
                "sizes": "140x140"
            }
        ],
        "start_url": "/",
        "display": "standalone",
        "gcm_sender_id": os.environ.get("GCM_SENDER_ID", "879549232238")
    })

def service_worker():
    return current_app.send_static_file("service_worker.js")
