import json

from flask import g, render_template, request, redirect, url_for
from sqlalchemy.orm import joinedload

from charat2.model import case_options, SearchCharacterGroup, SearchCharacterChoice
from charat2.model.connections import use_db


@use_db
def home():

    if g.user is None:
        return render_template("root/home_guest.html")

    search_character_groups = g.db.query(SearchCharacterGroup).order_by(
        SearchCharacterGroup.order,
    ).options(joinedload(SearchCharacterGroup.characters)).all()

    picky = set(_[0] for _ in g.db.query(
        SearchCharacterChoice.search_character_id,
    ).filter(
        SearchCharacterChoice.user_id == g.user.id,
    ).all())

    return render_template(
        "root/home.html",
        search_character_groups=search_character_groups,
        case_options=case_options,
        replacements=json.loads(g.user.replacements),
        regexes=json.loads(g.user.regexes),
        picky=picky,
    )

