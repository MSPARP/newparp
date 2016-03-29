from flask import g
import re
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from newparp.model import (
    CharacterTag,
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
