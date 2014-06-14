from flask import abort, g, jsonify, redirect, render_template, url_for
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers import alt_formats
from charat2.helpers.auth import login_required
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
    return redirect(url_for("character", character_id=character.id))


@alt_formats(set(["json"]))
@use_db
@login_required
def character(character_id, fmt=None):

    try:
        character = g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == character_id,
            UserCharacter.user_id == g.user.id,
        )).order_by(UserCharacter.title).one()
    except NoResultFound:
        abort(404)

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

    try:
        character = g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == character_id,
            UserCharacter.user_id == g.user.id,
        )).order_by(UserCharacter.title).one()
    except NoResultFound:
        abort(404)

    raise NotImplementedError


@use_db
@login_required
def delete_character_get(character_id):
    try:
        character = g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == character_id,
            UserCharacter.user_id == g.user.id,
        )).order_by(UserCharacter.title).one()
    except NoResultFound:
        abort(404)
    return render_template("rp/delete_character.html", character_id=character_id)


@use_db
@login_required
def delete_character_post(character_id):
    try:
        character = g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == character_id,
            UserCharacter.user_id == g.user.id,
        )).order_by(UserCharacter.title).one()
    except NoResultFound:
        abort(404)
    g.db.delete(character)
    return redirect(url_for("character_list"))

