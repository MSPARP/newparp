import os
import json
from flask import abort, g, jsonify, render_template, request, redirect, url_for
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers import alt_formats
from charat2.helpers.auth import log_in_required
from charat2.model import case_options, Character, GroupChat, SearchCharacter, SearchCharacterGroup, SearchCharacterChoice
from charat2.model.connections import use_db


@use_db
def home():

    if g.user is None:
        return render_template("rp/home_guest.html")

    characters = g.db.query(Character).filter(Character.user_id == g.user.id).order_by(Character.title).all()

    search_character_groups = g.db.query(SearchCharacterGroup).order_by(
        SearchCharacterGroup.order,
    ).options(joinedload(SearchCharacterGroup.characters)).all()

    picky = set(_[0] for _ in g.db.query(
        SearchCharacterChoice.search_character_id,
    ).filter(
        SearchCharacterChoice.user_id == g.user.id,
    ).all())

    return render_template(
        "rp/home.html",
        characters=characters,
        search_character_groups=search_character_groups,
        case_options=case_options,
        replacements=json.loads(g.user.replacements),
        regexes=json.loads(g.user.regexes),
        picky=picky,
    )


@alt_formats(set(["json"]))
@use_db
def rooms(fmt=None):

    rooms_query = g.db.query(GroupChat).filter(GroupChat.publicity == "listed")
    rooms = [(_, g.redis.scard("chat:%s:online" % _.id)) for _ in rooms_query]
    rooms.sort(key=lambda _: _[1], reverse=True)
    chat_dicts = []
    for chat, online in rooms:
        cd = chat.to_dict()
        cd["online"] = online
        chat_dicts.append(cd)
    if fmt == "json":
        return jsonify({
            "chats": chat_dicts,
        })

    return render_template("rp/rooms.html", rooms=chat_dicts)


def search_character_list():
    abort(404)


@use_db
def search_character(id):
    # XXX put this in redis?
    try:
        character = g.db.query(SearchCharacter).filter(SearchCharacter.id == id).one()
    except NoResultFound:
        abort(404)
    return jsonify(character.to_dict(include_options=True))

