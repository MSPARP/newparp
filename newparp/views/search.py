import json

from flask import (
    abort, g, jsonify, make_response, redirect, render_template, request,
    url_for
)
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4

from newparp.helpers import tags_to_set
from newparp.helpers.auth import log_in_required
from newparp.helpers.characters import validate_character_form
from newparp.model import case_options, GroupChat, SearchCharacter, SearchCharacterChoice, User
from newparp.model.connections import use_db, db_commit, db_disconnect
from newparp.model.validators import color_validator


@use_db
@log_in_required
def search_save():

    new_details = validate_character_form(request.form)
    g.user.search_character_id = new_details["search_character_id"]
    g.user.name = new_details["name"]
    g.user.acronym = new_details["acronym"]
    g.user.color = new_details["color"]
    g.user.quirk_prefix = new_details["quirk_prefix"]
    g.user.quirk_suffix = new_details["quirk_suffix"]
    g.user.case = new_details["case"]
    g.user.replacements = new_details["replacements"]
    g.user.regexes = new_details["regexes"]

    if request.form["style"] in User.search_style.type.enums:
        g.user.search_style = request.form["style"]

    level_filter = set()
    for level in GroupChat.level.type.enums:
        if level in request.form:
            level_filter.add(level)
    if not level_filter:
        level_filter.add("sfw")
    g.user.search_levels = level_filter

    search_filters = set()
    for search_filter in request.form.getlist("search_filter"):
        search_filter = search_filter.strip().lower()
        if search_filter:
            search_filters.add(search_filter)
        if len(search_filters) == 100:
            break
    g.user.search_filters = sorted(list(search_filters))

    all_character_ids = set(_[0] for _ in g.db.query(SearchCharacter.id).all())

    # Picky checkboxes
    g.db.query(SearchCharacterChoice).filter(SearchCharacterChoice.user_id == g.user.id).delete()
    if "use_picky" in request.form:
        for key in list(request.form.keys()):
            if not key.startswith("picky_"):
                continue
            try:
                character_id = int(key[6:])
            except:
                continue
            if character_id not in all_character_ids:
                continue
            g.db.add(SearchCharacterChoice(user_id=g.user.id, search_character_id=character_id))

    return redirect(url_for("rp_search"))


def _create_searcher():
    pipe = g.redis.pipeline()

    searcher_id = str(uuid4())
    pipe.set("searcher:%s:session_id" % searcher_id, g.session_id)
    pipe.expire("searcher:%s:session_id" % searcher_id, 30)

    pipe.set("searcher:%s:search_character_id" % searcher_id, g.user.search_character_id)
    pipe.expire("searcher:%s:search_character_id" % searcher_id, 30)

    pipe.hmset("searcher:%s:character" % searcher_id, {
        "name": g.user.name,
        "acronym": g.user.acronym,
        "color": g.user.color,
        "quirk_prefix": g.user.quirk_prefix,
        "quirk_suffix": g.user.quirk_suffix,
        "case": g.user.case,
        "replacements": g.user.replacements,
        "regexes": g.user.regexes,
    })
    pipe.expire("searcher:%s:character" % searcher_id, 30)

    pipe.set("searcher:%s:style" % searcher_id, g.user.search_style)
    pipe.expire("searcher:%s:style" % searcher_id, 30)

    pipe.sadd("searcher:%s:levels" % searcher_id, *g.user.search_levels)
    pipe.expire("searcher:%s:levels" % searcher_id, 30)

    if g.user.search_filters:
        pipe.rpush("searcher:%s:filters" % searcher_id, *g.user.search_filters) # XXX why is this a list and not a set?
    pipe.expire("searcher:%s:filters" % searcher_id, 30)

    choices = [_[0] for _ in g.db.query(
        SearchCharacterChoice.search_character_id,
    ).filter(
        SearchCharacterChoice.user_id == g.user.id,
    ).all()]
    if choices:
        pipe.sadd("searcher:%s:choices" % searcher_id, *choices)
    pipe.expire("searcher:%s:choices" % searcher_id, 30)

    pipe.execute()

    return searcher_id


@use_db
@log_in_required
def search_get():
    return render_template("search.html")


@use_db
@log_in_required
def search_post():
    return jsonify({ "id": _create_searcher() })

