import json

from flask import abort, g, make_response, redirect, render_template, request, url_for
from sqlalchemy import func
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
def new_search_character_group_post():
    name = request.form["name"].strip()
    if len(name) == 0:
        abort(400)
    order = (g.db.query(func.max(SearchCharacterGroup.order)).scalar() or 0) + 1
    g.db.add(SearchCharacterGroup(name=name, order=order))
    return redirect(url_for("rp_search_character_list"))


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


@use_db
@admin_required
def new_search_character_get():
    groups = g.db.query(SearchCharacterGroup).order_by(SearchCharacterGroup.order).all()
    return render_template(
        "rp/search_characters/search_character.html",
        groups=groups,
        case_options=case_options,
    )


@use_db
@admin_required
def new_search_character_post():
    new_details = validate_character_form(request.form)
    del new_details["search_character_id"]
    try:
        group = g.db.query(SearchCharacterGroup).filter(
            SearchCharacterGroup.id == request.form["group_id"],
        ).one()
    except NoResultFound:
        abort(404)
    order = (
        g.db.query(func.max(SearchCharacter.order))
        .filter(SearchCharacter.group_id == group.id)
        .scalar() or 0
    ) + 1
    new_search_character = SearchCharacter(
        group_id=group.id,
        order=order,
        text_preview=request.form["text_preview"],
        **new_details
    )
    g.db.add(new_search_character)
    return redirect(url_for("rp_search_character_list"))


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
    character.acronym = new_details["acronym"]
    character.color = new_details["color"]
    character.quirk_prefix = new_details["quirk_prefix"]
    character.quirk_suffix = new_details["quirk_suffix"]
    character.case = new_details["case"]
    character.replacements = new_details["replacements"]
    character.regexes = new_details["regexes"]
    character.text_preview = request.form["text_preview"]
    # Remember to clear the cache
    g.redis.delete("search_character:%s" % id)
    return redirect(url_for("rp_search_character_list"))

