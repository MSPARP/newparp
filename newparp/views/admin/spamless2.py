import paginate
import re

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.orm import joinedload_all

from newparp.helpers import alt_formats
from newparp.helpers.auth import permission_required
from newparp.model import Message, SpamFlag
from newparp.model.connections import use_db


@alt_formats({"json"})
@use_db
@permission_required("spamless")
def home(fmt=None, page=1):

    flags = (
        g.db.query(SpamFlag)
        .order_by(SpamFlag.id.desc())
        .options(
            joinedload_all(SpamFlag.message, Message.chat),
            joinedload_all(SpamFlag.message, Message.chat_user),
            joinedload_all(SpamFlag.message, Message.user),
        )
        .offset((page - 1) * 50).limit(50).all()
    )
    if not flags and page != 1:
        abort(404)

    flag_count = g.db.query(func.count("*")).select_from(SpamFlag).scalar()

    if fmt == "json":
        return jsonify({
            "flags": [_.to_dict() for _ in flags],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=flag_count,
        url_maker=lambda page: url_for("spamless2_home", page=page, **request.args),
    )

    return render_template(
        "admin/spamless2/home.html",
        flags=flags,
        paginator=paginator,
    )

