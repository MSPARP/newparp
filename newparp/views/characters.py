import json

from flask import g, jsonify, redirect, request, render_template, url_for
from sqlalchemy.orm import joinedload

from newparp.helpers import alt_formats
from newparp.helpers.auth import log_in_required
from newparp.helpers.characters import character_query, save_character_from_form, validate_character_form
from newparp.model import case_options, Character, CharacterTag, Request, SearchCharacter, SearchCharacterGroup
from newparp.model.connections import use_db


@alt_formats({"json"})
@use_db
@log_in_required
def character_list(fmt=None):

    characters = g.db.query(Character).filter(
        Character.user_id == g.user.id,
    ).order_by(Character.title, Character.id).all()

    if fmt == "json":
        return jsonify({ "characters": [_.to_dict(include_default=True) for _ in characters] })

    return render_template(
        "rp/characters/character_list.html",
        characters=characters,
    )


@use_db
@log_in_required
def new_character_get():

    search_character_groups = g.db.query(SearchCharacterGroup).order_by(
        SearchCharacterGroup.order,
    ).options(joinedload(SearchCharacterGroup.characters)).all()

    character_defaults = {_.name: _.default.arg for _ in Character.__table__.columns if _.default}
    character_defaults["search_character"] = search_character_groups[0].characters[0]

    return render_template(
        "rp/characters/character.html",
        character=character_defaults,
        replacements=[],
        regexes=[],
        character_tags={},
        search_character_groups=search_character_groups,
        case_options=case_options,
    )


@use_db
@log_in_required
def new_character_post():
    new_details = validate_character_form(request.form)
    g.db.add(Character(user_id=g.user.id, **new_details))
    return redirect(url_for("rp_character_list"))


@alt_formats({"json"})
@use_db
@log_in_required
def character(character_id, fmt=None):

    character = character_query(character_id, join_tags=True)

    search_character_groups = g.db.query(SearchCharacterGroup).order_by(
        SearchCharacterGroup.order,
    ).options(joinedload(SearchCharacterGroup.characters)).all()

    if fmt == "json":
        return jsonify(character.to_dict(include_default=True, include_options=True))

    return render_template(
        "rp/characters/character.html",
        character=character,
        replacements=json.loads(character.replacements),
        regexes=json.loads(character.regexes),
        character_tags={
            tag_type: ", ".join(tag["alias"] for tag in tags)
            for tag_type, tags in character.tags_by_type().iteritems()
        },
        search_character_groups=search_character_groups,
        case_options=case_options,
    )


@use_db
@log_in_required
def save_character(character_id):
    # In a separate function so we can call it from request search.
    character = save_character_from_form(character_id, request.form)
    return redirect(url_for("rp_character_list"))


@use_db
@log_in_required
def delete_character_get(character_id):
    character = character_query(character_id)
    return render_template("rp/characters/delete_character.html", character=character)


@use_db
@log_in_required
def delete_character_post(character_id):
    character = character_query(character_id)
    character_id = character.id
    if g.user.default_character_id == character_id:
        g.user.default_character_id = None
        g.db.flush()
    g.db.query(CharacterTag).filter(CharacterTag.character_id == character_id).delete()
    g.db.query(Request).filter(Request.character_id == character_id).update({ "character_id": None })
    # Don't use g.db.delete(character) because it does a load of extra queries
    # for foreign keys and stuff.
    g.db.query(Character).filter(Character.id == character_id).delete()
    return redirect(url_for("rp_character_list"))


@use_db
@log_in_required
def set_default_character(character_id):
    character = character_query(character_id)
    g.user.default_character = character
    return redirect(url_for("rp_character_list"))

