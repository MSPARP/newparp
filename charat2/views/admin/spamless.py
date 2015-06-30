from flask import abort, g, render_template
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from webhelpers import paginate

from charat2.helpers.auth import admin_required
from charat2.model import Message
from charat2.model.connections import use_db


@use_db
@admin_required
def home(fmt=None, page=1):

    messages = (
        g.db.query(Message)
        .filter(Message.spam_flag != None)
        .order_by(Message.id.desc())
        .options(joinedload(Message.chat), joinedload(Message.user))
        .offset((page - 1) * 50).limit(50).all()
    )

    if len(messages) == 0 and page != 1:
        abort(404)

    message_count = (
        g.db.query(func.count('*'))
        .select_from(Message)
        .filter(Message.spam_flag != None)
        .scalar()
    )

    if fmt == "json":
        return jsonify({
            "total": message_count,
            "messages": [_.to_dict(include_spam_flag=True) for _ in messages],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=message_count,
        url=lambda page: url_for("admin_spamless", page=page),
    )

    return render_template(
        "admin/spamless/home.html",
        messages=messages,
        paginator=paginator,
    )

