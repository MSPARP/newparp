import json

from flask import abort, g
from sqlalchemy.orm import joinedload_all
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_

from charat2.helpers.tags import character_tags_from_form
from charat2.model import case_options, Character, CharacterTag
from charat2.model.validators import color_validator


def character_query(character_id, join_tags=False):
    try:
        query = g.db.query(Character).filter(and_(
            Character.id == int(character_id),
            Character.user_id == g.user.id,
        ))
        if join_tags:
            query = query.options(joinedload_all("tags.tag"))
        return query.one()
    except NoResultFound:
        abort(404)
    except ValueError:
        abort(400)


def validate_character_form(form):

    # yeah this is just cut and pasted from chat_api.py
    # XXX MAKE chat_api.py USE THIS TOO

    # Don't allow a blank name.
    if form["name"] == "":
        abort(400)

    # Validate color.
    if not color_validator.match(form["color"]):
        abort(400)

    # Validate case.
    if form["case"] not in case_options:
        abort(400)

    # XXX PUT LENGTH LIMIT ON REPLACEMENTS?
    # Zip replacements.
    replacements = zip(
        form.getlist("quirk_from"),
        form.getlist("quirk_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    replacements = [_ for _ in replacements if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    json_replacements = json.dumps(replacements)

    # XXX PUT LENGTH LIMIT ON REGEXES?
    # Zip regexes.
    regexes = zip(
        form.getlist("regex_from"),
        form.getlist("regex_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    regexes = [_ for _ in regexes if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    json_regexes = json.dumps(regexes)

    return {
        # There are length limits on the front end so silently truncate these.
        "title": form["title"][:50],
        "name": form["name"][:50],
        "alias": form["alias"][:15],
        "color": form["color"],
        "quirk_prefix": form["quirk_prefix"][:50],
        "quirk_suffix": form["quirk_suffix"][:50],
        "case": form["case"],
        "replacements": json_replacements,
        "regexes": json_regexes,
    }


def save_character_from_form(character_id, form, new_details=None):

    character = character_query(character_id)

    if new_details is None:
        new_details = validate_character_form(form)

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

    g.db.query(CharacterTag).filter(CharacterTag.character_id == character.id).delete()
    character.tags += character_tags_from_form(form)

    return character

