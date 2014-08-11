import datetime

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound
from webhelpers import paginate

from charat2.helpers import alt_formats
from charat2.helpers.auth import login_required
from charat2.model import (
    Request,
    UserCharacter,
)
from charat2.model.connections import use_db


def _request_query(request_id, own=False):
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

    requests = g.db.query(Request).order_by(
        Request.posted.desc(),
    ).filter(
        Request.status == "posted",
    ).all()

    if fmt == "json":
        return jsonify({
            "requests": [_.to_dict(user=g.user) for _ in requests],
        })

    return render_template(
        "rp/request_search/request_list.html",
        page="all",
        requests=requests,
    )


@alt_formats(set(["json"]))
@use_db
@login_required
def your_request_list(fmt=None):

    requests = g.db.query(Request).order_by(
        Request.posted.desc(),
    ).filter(
        Request.user_id == g.user.id,
    ).all()

    if fmt == "json":
        return jsonify({
            "requests": [_.to_dict(user=g.user) for _ in requests],
        })

    return render_template(
        "rp/request_search/request_list.html",
        page="yours",
        requests=requests,
    )


def _new_request_form(error=None):

    characters = g.db.query(UserCharacter).filter(
        UserCharacter.user_id == g.user.id,
    ).order_by(UserCharacter.title, UserCharacter.id).all()

    selected_character = None
    if "character_id" in request.form:
        try:
            selected_character = int(request.form["character_id"])
        except ValueError:
            pass

    return render_template(
        "rp/request_search/new_request.html",
        characters=characters,
        selected_character=selected_character,
        error=error,
    )


@use_db
@login_required
def new_request_get():
    return _new_request_form()


@use_db
@login_required
def new_request_post():

    scenario = request.form["scenario"].strip()
    prompt = request.form["prompt"].strip()

    # At least one of prompt or scenario must be filled in.
    if len(scenario) == 0 and len(prompt) == 0:
        return _new_request_form(error="blank")

    # Just make the character none if the specified character isn't valid.
    try:
        character = g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == int(request.form["character_id"]),
            UserCharacter.user_id == g.user.id,
        )).one()
    except (ValueError, NoResultFound):
        character = None

    new_request = Request(
        user=g.user,
        status="draft" if "draft" in request.form else "posted",
        user_character=character,
        scenario=scenario,
        prompt=prompt,
    )
    g.db.add(new_request)
    g.db.flush()

    return redirect(url_for("rp_request", request_id=new_request.id))


@alt_formats(set(["json"]))
@use_db
@login_required
def request_detail(request_id, fmt=None):

    # Don't call it "request" because that overrides the flask request.
    search_request = _request_query(request_id)

    if fmt == "json":
        return jsonify(search_request.to_dict(user=g.user))

    return render_template(
        "rp/request_search/request.html",
        search_request=search_request,
    )


def answer_request(request_id):
    raise NotImplementedError


def _edit_request_form(search_request, error=None):

    characters = g.db.query(UserCharacter).filter(
        UserCharacter.user_id == g.user.id,
    ).order_by(UserCharacter.title, UserCharacter.id).all()

    selected_character = None
    if "character_id" in request.form:
        try:
            selected_character = int(request.form["character_id"])
        except ValueError:
            pass

    return render_template(
        "rp/request_search/edit_request.html",
        search_request=search_request,
        characters=characters,
        selected_character=selected_character,
        error=error,
    )


@use_db
@login_required
def edit_request_get(request_id):
    return _edit_request_form(_request_query(request_id, own=True))


@use_db
@login_required
def edit_request_post(request_id):

    search_request = _request_query(request_id, own=True)

    scenario = request.form["scenario"].strip()
    prompt = request.form["prompt"].strip()

    # At least one of prompt or scenario must be filled in.
    if len(scenario) == 0 and len(prompt) == 0:
        return _edit_request_form(search_request, error="blank")

    # Just make the character none if the specified character isn't valid.
    try:
        character = g.db.query(UserCharacter).filter(and_(
            UserCharacter.id == int(request.form["character_id"]),
            UserCharacter.user_id == g.user.id,
        )).one()
    except (ValueError, NoResultFound):
        character = None

    search_request.scenario = scenario
    search_request.prompt = prompt
    search_request.user_character = character

    if "draft" in request.form:
        search_request.status = "draft"
    elif search_request.status != "posted":
        search_request.status = "posted"
        # Bump the date if the request is being re-posted.
        search_request.posted = datetime.datetime.now()

    return redirect(url_for("rp_request", request_id=search_request.id))


@use_db
@login_required
def delete_request_get(request_id):
    return render_template(
        "rp/request_search/delete_request.html",
        search_request=_request_query(request_id, own=True),
    )


@use_db
@login_required
def delete_request_post(request_id):
    search_request = _request_query(request_id, own=True)
    g.db.delete(search_request)
    g.db.commit()
    return redirect(url_for("rp_your_request_list"))

