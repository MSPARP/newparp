from flask import g, redirect, render_template, url_for

from charat2.helpers.auth import login_required
from charat2.model import UserCharacter
from charat2.model.connections import use_db

@use_db
@login_required
def character_list():

    return render_template(
        "rp/character_list.html",
        characters=g.db.query(UserCharacter).filter(
            UserCharacter.user_id==g.user.id,
        ).order_by(UserCharacter.title).all(),
    )


@use_db
@login_required
def new_character():
    character = UserCharacter(user_id=g.user.id, title="Untitled character")
    g.db.add(character)
    g.db.flush()
    return redirect(url_for("character", character_id=character.id))


@use_db
@login_required
def character(character_id):
    raise NotImplementedError

