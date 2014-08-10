from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy.orm.exc import NoResultFound
from webhelpers import paginate

from charat2.helpers import alt_formats
from charat2.helpers.auth import login_required
from charat2.model import (
    Request,
)
from charat2.model.connections import use_db

@alt_formats(set(["json"]))
@use_db
@login_required
def request_list(fmt=None):

    requests = g.db.query(Request).order_by(
        Request.posted.desc(),
    ).filter(
        Request.status == "posted",
    ).all()

    if fmt == "json":
        return jsonify({
            "requests": [_.to_dict() for _ in requests],
        })

    return render_template(
        "rp/request_search/request_list.html",
        requests=requests,
    )


def your_request_list():
    raise NotImplementedError


def new_request_get():
    raise NotImplementedError


def new_request_post():
    raise NotImplementedError


def request(request_id):
    raise NotImplementedError


def answer_request(request_id):
    raise NotImplementedError


def edit_request_get(request_id):
    raise NotImplementedError


def edit_request_post(request_id):
    raise NotImplementedError


def delete_request_get(request_id):
    raise NotImplementedError


def delete_request_post(request_id):
    raise NotImplementedError

