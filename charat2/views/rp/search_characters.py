import json

from flask import abort, g, make_response, render_template
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.auth import admin_required
from charat2.model import case_options, SearchCharacter, SearchCharacterGroup, SearchCharacterChoice, User
from charat2.model.connections import use_db, db_connect


@use_db
@admin_required
def search_character_list():
    return render_template(
        "rp/search_characters/search_character_list.html",
        search_character_groups=g.db.query(SearchCharacterGroup).order_by(
            SearchCharacterGroup.order,
        ).options(joinedload(SearchCharacterGroup.characters)).all(),
    )


@use_db
@admin_required
def search_character(id):
    raise NotImplementedError


def search_character_json(id):

    character_json = g.redis.get("search_character:%s" % id)

    if character_json is None:
        db_connect()
        try:
            character = g.db.query(SearchCharacter).filter(SearchCharacter.id == id).one()
        except NoResultFound:
            abort(404)
        character_json = json.dumps(character.to_dict(include_options=True))
        g.redis.set("search_character:%s" % id, character_json)
        g.redis.expire("search_character:%s" % id, 3600)

    resp = make_response(character_json)
    resp.headers["Content-type"] = "application/json"
    return resp

