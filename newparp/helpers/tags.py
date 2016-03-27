from flask import g
import re
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from newparp.model import (
    CharacterTag,
    RequestTag,
    Tag,
)

special_char_regex = re.compile("[\\ \\./]+")
underscore_strip_regex = re.compile("^_+|_+$")


def name_from_alias(alias):
    # 1. Change to lowercase.
    # 2. Change spaces to underscores.
    # 3. Change . and / to underscores because they screw up the routing.
    # 4. Strip extra underscores from the start and end.
    return underscore_strip_regex.sub(
        "",
        special_char_regex.sub("_", alias)
    ).lower()


def character_tags_from_form(form):

    tag_dict = {}

    for tag_type in ("fandom", "character", "gender"):
        for alias in form[tag_type].split(","):
            alias = alias.strip()
            if alias == "":
                continue
            name = name_from_alias(alias)
            if name == "":
                continue
            tag_dict[(tag_type, name)] = alias

    character_tags = []
    used_ids = set()

    for (tag_type, name), alias in tag_dict.iteritems():
        try:
            tag = g.db.query(Tag).filter(and_(
                Tag.type == tag_type, Tag.name == name,
            )).one()
        except NoResultFound:
            tag = Tag(type=tag_type, name=name)
            g.db.add(tag)
            g.db.flush()
        tag_id = (tag.synonym_id or tag.id)
        # Remember IDs to skip synonyms.
        if tag_id in used_ids:
            continue
        used_ids.add(tag_id)
        character_tags.append(CharacterTag(tag_id=tag_id, alias=alias))

    return character_tags


def request_tags_from_character(character):
    return [
        RequestTag(tag_id=character_tag.tag_id, alias=character_tag.alias)
        for character_tag in character.tags
    ]


def request_tags_from_form(form, include_character_tags=False):

    tag_dict = {}

    for tag_type in Tag.type_options:

        # Enforce preset values for maturity.
        if tag_type == "maturity":
            name = form["maturity"]
            if name in Tag.maturity_names:
                tag_dict[("maturity", name)] = name.capitalize()
            else:
                tag_dict[("maturity", "general")] = "General"
            continue

        # Enforce preset values for type.
        elif tag_type == "type":
            for name in Tag.type_names:
                if "type_" + name in form:
                    tag_dict[("type", name)] = name.capitalize()
            continue

        if tag_type in ("fandom", "character", "gender") and not include_character_tags:
            continue

        for alias in form[tag_type].split(","):
            alias = alias.strip()
            if alias == "":
                continue
            name = name_from_alias(alias)
            if name == "":
                continue
            tag_dict[(tag_type, name)] = alias

    request_tags = []
    used_ids = set()

    for (tag_type, name), alias in tag_dict.iteritems():
        try:
            tag = g.db.query(Tag).filter(and_(
                Tag.type == tag_type, Tag.name == name,
            )).one()
        except NoResultFound:
            tag = Tag(type=tag_type, name=name)
        tag_id = (tag.synonym_id or tag.id)
        # Remember IDs to skip synonyms.
        if tag_id in used_ids:
            continue
        used_ids.add(tag_id)
        request_tags.append(RequestTag(tag_id=tag_id, alias=alias))

    return request_tags

