from flask import g

from charat2.model import SearchCharacter
from charat2.model.connections import use_db

@use_db
def health():
    g.redis.set("health", 1)
    g.db.query(SearchCharacter).first()
    return "ok"

