import json

from flask import abort, g, make_response, redirect, render_template, request, url_for
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.auth import admin_required
from charat2.helpers.characters import validate_character_form
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
    try:
        character = g.db.query(SearchCharacter).filter(SearchCharacter.id == id).one()
    except NoResultFound:
        abort(404)
    return render_template(
        "rp/search_characters/search_character.html",
        character=character.to_dict(include_options=True),
        case_options=case_options,
    )


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


@use_db
@admin_required
def save_search_character(id):
    try:
        character = g.db.query(SearchCharacter).filter(SearchCharacter.id == id).one()
    except NoResultFound:
        abort(404)
    new_details = validate_character_form(request.form)
    # Ignore a blank title.
    if new_details["title"] != "":
        character.title = new_details["title"]
    character.name = new_details["name"]
    character.alias = new_details["alias"]
    character.color = new_details["color"]
    character.quirk_prefix = new_details["quirk_prefix"]
    character.quirk_suffix = new_details["quirk_suffix"]
    character.case = new_details["case"]
    character.replacements = new_details["replacements"]
    character.regexes = new_details["regexes"]
    # Remember to clear the cache
    g.redis.delete("search_character:%s" % id)
    return redirect(url_for("rp_search_character_list"))

