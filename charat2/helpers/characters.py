import json

from flask import abort, g, request
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_

from charat2.model import case_options, UserCharacter
from charat2.model.validators import color_validator

def user_character_query(character_id):
    try:
        return g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == character_id,
            UserCharacter.user_id == g.user.id,
        )).one()
    except NoResultFound:
        abort(404)

def save_character_from_form(character_id):

    character = user_character_query(character_id)

    # yeah this is just cut and pasted from chat_api.py

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
    # Also ignore a blank title.
    if request.form["title"] != "":
        character.title = request.form["title"][:50]
    character.name = request.form["name"][:50]
    character.alias = request.form["alias"][:15]
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

    return character

