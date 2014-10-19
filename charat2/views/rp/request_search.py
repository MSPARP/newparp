import datetime
import json

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload, joinedload_all
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4
from webhelpers import paginate

from charat2.helpers import alt_formats
from charat2.helpers.auth import log_in_required
from charat2.helpers.characters import (
    character_query,
    validate_character_form,
    save_character_from_form,
)
from charat2.helpers.tags import request_tags_from_character, request_tags_from_form
from charat2.model import (
    case_options,
    ChatUser,
    Message,
    Request,
    RequestTag,
    RequestedChat,
    Tag,
    Character,
)
from charat2.model.connections import use_db


def _own_request_query(request_id):
    try:
        search_request = g.db.query(Request).filter(
            Request.id == request_id,
        ).options(joinedload_all("tags.tag")).one()
    except NoResultFound:
        abort(404)
    if search_request.user != g.user:
        abort(404)
    return search_request


@alt_formats(set(["json"]))
@use_db
@log_in_required
def request_list(fmt=None, page=1):

    requests = g.db.query(Request).order_by(
        Request.posted.desc(),
    ).filter(
        Request.status == "posted",
    ).options(
        joinedload_all("tags.tag"),
    ).offset((page - 1) * 50).limit(50).all()

    if len(requests) == 0 and page != 1:
        abort(404)

    request_count = g.db.query(func.count('*')).select_from(Request).filter(
        Request.status == "posted",
    ).scalar()

    if fmt == "json":
        return jsonify({
            "total": request_count,
            "requests": [_.to_dict(user=g.user) for _ in requests],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=request_count,
        url=lambda page: url_for("rp_request_list", page=page),
    )

    return render_template(
        "rp/request_search/request_list.html",
        page="all",
        requests=requests,
        paginator=paginator,
    )


@alt_formats(set(["json"]))
@use_db
@log_in_required
def your_request_list(fmt=None, page=1):

    requests = g.db.query(Request).order_by(
        Request.posted.desc(),
    ).filter(
        Request.user_id == g.user.id,
    ).options(
        joinedload_all("tags.tag"),
    ).offset((page - 1) * 50).limit(50).all()

    if len(requests) == 0 and page != 1:
        abort(404)

    request_count = g.db.query(func.count('*')).select_from(Request).filter(
        Request.user_id == g.user.id,
    ).scalar()

    if fmt == "json":
        return jsonify({
            "total": request_count,
            "requests": [_.to_dict(user=g.user) for _ in requests],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=request_count,
        url=lambda page: url_for("rp_your_request_list", page=page),
    )

    return render_template(
        "rp/request_search/request_list.html",
        page="yours",
        requests=requests,
        paginator=paginator,
    )


@alt_formats(set(["json"]))
@use_db
@log_in_required
def tagged_request_list(tag_type, name, fmt=None, page=1):

    # Redirect to lowercase and replace spaces.
    replaced_name = name.lower().replace(" ", "_")[:50]
    if replaced_name != name:
        return redirect(url_for(
            "rp_tagged_request_list",
            tag_type=tag_type,
            name=replaced_name,
            fmt=fmt,
            page=page if page != 1 else None,
        ))

    try:
        tag = g.db.query(Tag).filter(and_(
            Tag.type == tag_type,
            Tag.name == name,
        )).one()
    except NoResultFound:
        abort(404)

    requests = g.db.query(Request).order_by(
        Request.posted.desc(),
    ).join(
        RequestTag,
        Request.id == RequestTag.request_id,
    ).filter(and_(
        RequestTag.tag_id == tag.id,
        Request.status == "posted",
    )).options(
        joinedload_all("tags.tag"),
    ).offset((page - 1) * 50).limit(50).all()

    if len(requests) == 0 and page != 1:
        abort(404)

    request_count = g.db.query(func.count('*')).select_from(RequestTag).filter(
        RequestTag.tag_id == tag.id,
    ).scalar()

    if fmt == "json":
        return jsonify({
            "total": request_count,
            "requests": [_.to_dict(user=g.user) for _ in requests],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=request_count,
        url=lambda page: url_for("rp_tagged_request_list", tag_type=tag_type, name=name, page=page),
    )

    return render_template(
        "rp/request_search/request_list.html",
        page="tag",
        tag=tag,
        requests=requests,
        paginator=paginator,
    )


@use_db
@log_in_required
def new_request_get():

    characters = g.db.query(Character).filter(
        Character.user_id == g.user.id,
    ).order_by(Character.title, Character.id).all()

    return render_template(
        "rp/request_search/new_request.html",
        case_options=case_options,
        Tag=Tag,
        characters=characters,
    )


@use_db
@log_in_required
def new_request_post():

    scenario = request.form["scenario"].strip()
    prompt = request.form["prompt"].strip()

    # At least one of prompt or scenario must be filled in.
    if len(scenario) == 0 and len(prompt) == 0:
        abort(400)

    status = "draft" if "draft" in request.form else "posted"

    new_or_saved_character = request.form["new_or_saved_character"]
    edit_character = "edit_character" in request.form
    save_character_as = request.form["save_character_as"]

    # Use saved character verbatim.
    if new_or_saved_character == "saved" and not edit_character:

        character = character_query(request.form["character_id"], join_tags=True)
        # XXX consider making a classmethod for this like with user_chat
        new_request = Request(
            user=g.user,
            status=status,
            character=character,
            name=character.name,
            alias=character.alias,
            color=character.color,
            quirk_prefix=character.quirk_prefix,
            quirk_suffix=character.quirk_suffix,
            case=character.case,
            replacements=character.replacements,
            regexes=character.regexes,
            scenario=scenario,
            prompt=prompt,
        )

        new_request.tags = request_tags_from_character(character)
        new_request.tags += request_tags_from_form(request.form)

    # Otherwise rely on the form data.
    else:

        character = None
        character_details = validate_character_form(request.form)

        # Update existing character.
        if new_or_saved_character == "saved" and save_character_as == "update":
            character = save_character_from_form(request.form["character_id"], request.form)

        # Create new character.
        elif save_character_as == "new":
            if character_details["title"] == "":
                character_details["title"] == "Untitled character"
            character = Character(user=g.user, **character_details)
            g.db.add(character)
            g.db.flush()

        # Neither.
        elif save_character_as == "temp":
            pass

        # oh god how did this get here I am not good with computer
        else:
            abort(400)

        new_request = Request(
            user=g.user,
            status=status,
            character=character,
            scenario=scenario,
            prompt=prompt,
        )

        # The title and tag attributes from the character aren't needed on the
        # request, so only copy the attributes Requests actually have.
        for key, value in character_details.iteritems():
            if hasattr(new_request, key):
                setattr(new_request, key, value)

        if character is not None:
            new_request.tags = request_tags_from_character(character)
            new_request.tags += request_tags_from_form(request.form)
        else:
            new_request.tags = request_tags_from_form(request.form, include_character_tags=True)

    g.db.add(new_request)

    return redirect(url_for("rp_your_request_list"))


@use_db
@log_in_required
def answer_request(request_id):

    try:
        search_request = g.db.query(Request).filter(
            Request.id == request_id,
        ).options(
            joinedload(Request.user),
        ).one()
    except NoResultFound:
        abort(404)

    if search_request.status != "posted" or search_request.user == g.user:
        abort(404)

    new_chat = RequestedChat(url=str(uuid4()).replace("-", ""))
    g.db.add(new_chat)
    g.db.flush()

    new_chat_user = ChatUser(
        user=search_request.user,
        chat=new_chat,
        name=search_request.name,
        alias=search_request.alias,
        color=search_request.color,
        quirk_prefix=search_request.quirk_prefix,
        quirk_suffix=search_request.quirk_suffix,
        case=search_request.case,
        replacements=search_request.replacements,
        regexes=search_request.regexes,
        # XXX USER VARIABLES
    )
    g.db.add(new_chat_user)

    if len(search_request.scenario) > 0:
        g.db.add(Message(
            chat=new_chat,
            type="search_info",
            alias="Scenario",
            text=search_request.scenario,
        ))

    if len(search_request.prompt) > 0:
        g.db.add(Message(
            chat=new_chat,
            user=search_request.user,
            type="ic",
            color=new_chat_user.color,
            alias=new_chat_user.alias,
            name=new_chat_user.name,
            text=search_request.prompt,
        ))

    return redirect(url_for("rp_chat", url=new_chat.url))


@use_db
@log_in_required
def edit_request_get(request_id):

    search_request = _own_request_query(request_id)

    characters = g.db.query(Character).filter(
        Character.user_id == g.user.id,
    ).order_by(Character.title, Character.id).all()

    tags_by_type = search_request.tags_by_type()

    try:
        search_request_maturity = tags_by_type["maturity"][0]["name"]
    except IndexError:
        search_request_maturity = None

    replacements = json.loads(search_request.replacements)
    regexes = json.loads(search_request.regexes)

    return render_template(
        "rp/request_search/edit_request.html",
        case_options=case_options,
        search_request=search_request,
        search_request_tags={
            tag_type: ", ".join(tag["alias"] for tag in tags)
            for tag_type, tags in tags_by_type.iteritems()
        },
        search_request_maturity=search_request_maturity,
        search_request_types=set(_["name"] for _ in tags_by_type["type"]),
        Tag=Tag,
        characters=characters,
        replacements=replacements,
        regexes=regexes,
    )


@use_db
@log_in_required
def edit_request_post(request_id):

    search_request = _own_request_query(request_id)

    search_request.scenario = request.form["scenario"].strip()
    search_request.prompt = request.form["prompt"].strip()

    # At least one of prompt or scenario must be filled in.
    if len(search_request.scenario) == 0 and len(search_request.prompt) == 0:
        abort(400)

    if "draft" in request.form:
        search_request.status = "draft"
    elif search_request.status != "posted":
        search_request.status = "posted"
        # Bump the date if the request is being re-posted.
        search_request.posted = datetime.datetime.now()

    new_or_saved_character = request.form["new_or_saved_character"]
    edit_character = "edit_character" in request.form
    save_character_as = request.form["save_character_as"]

    g.db.query(RequestTag).filter(RequestTag.request_id == search_request.id).delete()

    # Use saved character verbatim.
    if new_or_saved_character == "saved" and not edit_character:

        character = character_query(request.form["character_id"], join_tags=True)

        search_request.character=character
        search_request.name=character.name
        search_request.alias=character.alias
        search_request.color=character.color
        search_request.quirk_prefix=character.quirk_prefix
        search_request.quirk_suffix=character.quirk_suffix
        search_request.case=character.case
        search_request.replacements=character.replacements
        search_request.regexes=character.regexes

        search_request.tags += request_tags_from_character(character)
        search_request.tags += request_tags_from_form(request.form)

    # Otherwise rely on the form data.
    else:

        character = None
        character_details = validate_character_form(request.form)

        # Update existing character.
        if new_or_saved_character == "saved" and save_character_as == "update":
            character = save_character_from_form(request.form["character_id"], request.form)

        # Create new character.
        elif save_character_as == "new":
            if character_details["title"] == "":
                character_details["title"] == "Untitled character"
            character = Character(user=g.user, **character_details)
            g.db.add(character)
            g.db.flush()

        # Neither.
        elif save_character_as == "temp":
            pass

        # oh god how did this get here I am not good with computer
        else:
            abort(400)

        # The title and tag attributes from the character aren't needed on the
        # request, so only copy the attributes Requests actually have.
        for key, value in character_details.iteritems():
            if hasattr(search_request, key):
                setattr(search_request, key, value)

        if character is not None:
            search_request.tags += request_tags_from_character(character)
            search_request.tags += request_tags_from_form(request.form)
        else:
            search_request.tags += request_tags_from_form(request.form, include_character_tags=True)

    return redirect(url_for("rp_edit_request_get", request_id=search_request.id))


@use_db
@log_in_required
def delete_request_get(request_id):
    return render_template(
        "rp/request_search/delete_request.html",
        search_request=_own_request_query(request_id),
    )


@use_db
@log_in_required
def delete_request_post(request_id):
    search_request = _own_request_query(request_id)
    g.db.query(RequestTag).filter(RequestTag.request_id == search_request.id).delete()
    g.db.query(Request).filter(Request.id == search_request.id).delete()
    g.db.commit()
    return redirect(url_for("rp_your_request_list"))

