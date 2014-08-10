from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy.orm.exc import NoResultFound
from webhelpers import paginate

from charat2.helpers import alt_formats
from charat2.helpers.auth import login_required
from charat2.model import (
    Request,
)
from charat2.model.connections import use_db


def request_query(request_id, own=False):
    try:
        request = g.db.query(Request).filter(Request.id == request_id).one()
    except NoResultFound:
        abort(404)
    if own and request.user != g.user:
        abort(404)
    elif request.status == "draft" and request.user != g.user:
        abort(404)
    return request


@alt_formats(set(["json"]))
@use_db
@login_required
def request_list(fmt=None):
    print request.matched_route
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


@alt_formats(set(["json"]))
@use_db
@login_required
def request_detail(request_id, fmt=None):

    # Don't call it "request" because that overrides the flask request.
    search_request = request_query(request_id)

    if fmt == "json":
        return jsonify(request.to_dict())

    return render_template(
        "rp/request_search/request.html",
        search_request=search_request,
    )


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

