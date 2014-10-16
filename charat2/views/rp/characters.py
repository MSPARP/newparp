from flask import g, jsonify, redirect, render_template, url_for

from charat2.helpers import alt_formats
from charat2.helpers.auth import login_required
from charat2.helpers.characters import user_character_query, save_character_from_form
from charat2.model import case_options, UserCharacter
from charat2.model.connections import use_db


@alt_formats(set(["json"]))
@use_db
@login_required
def character_list(fmt=None):

    characters = g.db.query(UserCharacter).filter(
        UserCharacter.user_id == g.user.id,
    ).order_by(UserCharacter.title, UserCharacter.id).all()

    if fmt == "json":
        return jsonify({ "characters": [_.to_dict() for _ in characters] })

    return render_template(
        "rp/character_list.html",
        characters=characters,
    )


@use_db
@login_required
def new_character():
    character = UserCharacter(user_id=g.user.id, title="Untitled character")
    g.db.add(character)
    g.db.flush()
    return redirect(url_for("rp_character", character_id=character.id))


@alt_formats(set(["json"]))
@use_db
@login_required
def character(character_id, fmt=None):

    character = user_character_query(character_id)

    if fmt == "json":
        return jsonify(character.to_dict(include_options=True))

    return render_template(
        "rp/character.html",
        character=character.to_dict(include_options=True),
        case_options=case_options,
        tags_fandom = ", ".join(_ for _ in character.fandom),
        tags_character = ", ".join(_ for _ in character.character),
        tags_gender = ", ".join(_ for _ in character.gender),
    )


@use_db
@login_required
def save_character(character_id):
    # In a separate function so we can call it from request search.
    character = save_character_from_form(character_id)
    return redirect(url_for("rp_character", character_id=character.id))


@use_db
@login_required
def delete_character_get(character_id):
    character = user_character_query(character_id)
    return render_template("rp/delete_character.html", character_id=character_id)


@use_db
@login_required
def delete_character_post(character_id):
    character = user_character_query(character_id)
    if character == g.user.default_character:
        g.user.default_character_id = None
        g.db.flush()
    g.db.delete(character)
    return redirect(url_for("rp_character_list"))


@use_db
@login_required
def set_default_character(character_id):
    character = user_character_query(character_id)
    g.user.default_character = character
    return redirect(url_for("rp_character_list"))

