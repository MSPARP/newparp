import json

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers import alt_formats
from charat2.helpers.auth import login_required
from charat2.model import case_options, UserCharacter
from charat2.model.connections import use_db
from charat2.model.validators import color_validator


def user_character_query(character_id):
    try:
        return g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == character_id,
            UserCharacter.user_id == g.user.id,
        )).order_by(UserCharacter.title).one()
    except NoResultFound:
        abort(404)


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
    return redirect(url_for("character", character_id=character.id))


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
    )


@use_db
@login_required
def save_character(character_id):

    character = user_character_query(character_id)

    # yeah this is just cut and pasted from chat_api.py

    # Don't allow a blank title.
    if request.form["title"] == "":
        abort(400)

    # Don't allow a blank name.
    if request.form["name"] == "":
        abort(400)

    # Validate color.
    if not color_validator.match(request.form["color"]):
        abort(400)
    character.color = request.form["color"]

    # Validate case.
    if request.form["case"] not in case_options:
        abort(400)
    character.case = request.form["case"]

    # There are length limits on the front end so just silently truncate these.
    character.title = request.form["title"][:50]
    character.name = request.form["name"][:50]
    character.acronym = request.form["acronym"][:15]
    character.quirk_prefix = request.form["quirk_prefix"][:50]
    character.quirk_suffix = request.form["quirk_suffix"][:50]

    # XXX PUT LENGTH LIMIT ON REPLACEMENTS?
    # Zip replacements.
    replacements = zip(
        request.form.getlist("quirk_from"),
        request.form.getlist("quirk_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    replacements = [_ for _ in replacements if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    character.replacements = json.dumps(replacements)

    # XXX PUT LENGTH LIMIT ON REGEXES?
    # Zip regexes.
    regexes = zip(
        request.form.getlist("regex_from"),
        request.form.getlist("regex_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    regexes = [_ for _ in regexes if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    character.regexes = json.dumps(regexes)

    return redirect(url_for("character", character_id=character.id))


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
    return redirect(url_for("character_list"))


@use_db
@login_required
def set_default_character(character_id):
    character = user_character_query(character_id)
    g.user.default_character = character
    return redirect(url_for("character_list"))

