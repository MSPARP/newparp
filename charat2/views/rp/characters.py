from flask import g, render_template

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

