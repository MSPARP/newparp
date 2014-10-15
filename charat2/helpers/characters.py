import json

from flask import abort, g, request
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_

from charat2.helpers import tags_to_set
from charat2.model import case_options, UserCharacter
from charat2.model.validators import color_validator


def user_character_query(character_id):
    try:
        return g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == int(character_id),
            UserCharacter.user_id == g.user.id,
        )).one()
    except NoResultFound:
        abort(404)
    except ValueError:
        abort(400)


def validate_character_form():

    # yeah this is just cut and pasted from chat_api.py
    # XXX MAKE chat_api.py USE THIS TOO

    # Don't allow a blank name.
    if request.form["name"] == "":
        abort(400)

    # Validate color.
    if not color_validator.match(request.form["color"]):
        abort(400)

    # Validate case.
    if request.form["case"] not in case_options:
        abort(400)

    # XXX PUT LENGTH LIMIT ON REPLACEMENTS?
    # Zip replacements.
    replacements = zip(
        request.form.getlist("quirk_from"),
        request.form.getlist("quirk_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    replacements = [_ for _ in replacements if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    json_replacements = json.dumps(replacements)

    # XXX PUT LENGTH LIMIT ON REGEXES?
    # Zip regexes.
    regexes = zip(
        request.form.getlist("regex_from"),
        request.form.getlist("regex_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    regexes = [_ for _ in regexes if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    json_regexes = json.dumps(regexes)

    fandom = tags_to_set(request.form["fandom"])
    character = tags_to_set(request.form["character"])
    gender = tags_to_set(request.form["gender"])

    return {
        # There are length limits on the front end so silently truncate these.
        "title": request.form["title"][:50],
        "name": request.form["name"][:50],
        "alias": request.form["alias"][:15],
        "color": request.form["color"],
        "quirk_prefix": request.form["quirk_prefix"][:50],
        "quirk_suffix": request.form["quirk_suffix"][:50],
        "case": request.form["case"],
        "replacements": json_replacements,
        "regexes": json_regexes,
        "fandom": fandom,
        "character": character,
        "gender": gender,
    }


def save_character_from_form(character_id, new_details=None):

    character = user_character_query(character_id)

    if new_details is None:
        new_details = validate_character_form()

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
    character.fandom = new_details["fandom"]
    character.character = new_details["character"]
    character.gender = new_details["gender"]

    return character

