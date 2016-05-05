import paginate
import re

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from newparp.helpers import alt_formats
from newparp.helpers.auth import permission_required
from newparp.model import Message, SpamFlag
from newparp.model.connections import use_db


@alt_formats({"json"})
@use_db
@permission_required("spamless")
def home(fmt=None, page=1):

    flags = g.db.query(SpamFlag).order_by(SpamFlag.id.desc()).all()

    if fmt == "json":
        return jsonify({
            "flags": [_.to_dict() for _ in flags],
        })

    return render_template(
        "admin/spamless2/home.html",
        flags=flags,
    )

