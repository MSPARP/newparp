from flask import g

from newparp.model import SearchCharacter
from newparp.model.connections import use_db

@use_db
def health():
    g.redis.set("health", 1)
    g.db.query(SearchCharacter).first()
    return "ok"

