from flask import g, jsonify, redirect, request, render_template, url_for
from sqlalchemy.orm import joinedload

from charat2.helpers import alt_formats
from charat2.helpers.auth import log_in_required
from charat2.helpers.characters import character_query, save_character_from_form
from charat2.model import case_options, Character, CharacterTag, Request, SearchCharacter, SearchCharacterGroup
from charat2.model.connections import use_db


@alt_formats(set(["json"]))
@use_db
@log_in_required
def character_list(fmt=None):

    characters = g.db.query(Character).filter(
        Character.user_id == g.user.id,
    ).order_by(Character.title, Character.id).all()

    if fmt == "json":
        return jsonify({ "characters": [_.to_dict() for _ in characters] })

    return render_template(
        "rp/characters/character_list.html",
        characters=characters,
    )


@use_db
@log_in_required
def new_character():
    character = Character(user_id=g.user.id, title="Untitled character")
    g.db.add(character)
    g.db.flush()
    return redirect(url_for("rp_character", character_id=character.id))


@alt_formats(set(["json"]))
@use_db
@log_in_required
def character(character_id, fmt=None):

    character = character_query(character_id, join_tags=True)

    search_character_groups = g.db.query(SearchCharacterGroup).order_by(
        SearchCharacterGroup.order,
    ).options(joinedload(SearchCharacterGroup.characters)).all()

    if fmt == "json":
        return jsonify(character.to_dict(include_options=True))

    return render_template(
        "rp/characters/character.html",
        character=character.to_dict(include_options=True),
        search_character_groups=search_character_groups,
        case_options=case_options,
        character_tags={
            tag_type: ", ".join(tag["alias"] for tag in tags)
            for tag_type, tags in character.tags_by_type().iteritems()
        },
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
    g.db.query(Request).filter(Request.character_id==character_id).update({ "character_id": None })
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

