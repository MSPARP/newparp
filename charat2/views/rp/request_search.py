import datetime
import re

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload, joinedload_all
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4
from webhelpers import paginate

from charat2.helpers import alt_formats
from charat2.helpers.auth import login_required
from charat2.helpers.characters import new_character_from_form, save_character_from_form
from charat2.model import (
    case_options,
    ChatUser,
    Message,
    Request,
    RequestTag,
    RequestedChat,
    Tag,
    UserCharacter,
)
from charat2.model.connections import use_db


special_char_regex = re.compile("[\\ \\./]+")
underscore_strip_regex = re.compile("^_+|_+$")


def _name_from_alias(alias):
    # 1. Change to lowercase.
    # 2. Change spaces to underscores.
    # 3. Change . and / to underscores because they screw up the routing.
    # 4. Strip extra underscores from the start and end.
    return underscore_strip_regex.sub(
        "",
        special_char_regex.sub("_", alias)
    ).lower()


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


def _tags_from_form(form):

    tag_dict = {}

    for tag_type in Tag.type_options:

        # Enforce preset values for maturity.
        if tag_type == "maturity":
            name = form["maturity"]
            if name in Tag.maturity_names:
                tag_dict[("maturity", name)] = name.capitalize()
            else:
                tag_dict[("maturity", "general")] = "General"
            continue

        # Enforce preset values for type.
        elif tag_type == "type":
            for name in Tag.type_names:
                if "type_" + name in form:
                    tag_dict[("type", name)] = name.capitalize()
            continue

        for alias in form[tag_type].split(","):
            alias = alias.strip()
            if alias == "":
                continue
            name = _name_from_alias(alias)
            if name == "":
                continue
            tag_dict[(tag_type, name)] = alias

    request_tags = []

    for (tag_type, name), alias in tag_dict.iteritems():
        try:
            tag = g.db.query(Tag).filter(and_(
                Tag.type == tag_type, Tag.name == name,
            )).one()
        except:
            tag = Tag(type=tag_type, name=name)
        request_tags.append(RequestTag(tag=tag, alias=alias))

    return request_tags


@alt_formats(set(["json"]))
@use_db
@login_required
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
@login_required
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
@login_required
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
        case_options=case_options,
        Tag=Tag,
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

    new_or_saved_character = request.form["new_or_saved_character"]
    edit_character = "edit_character" in request.form
    save_character_as = request.form["save_character_as"]


    if new_or_saved_character == "new":
        if save_character_as == "new":
            print "CREATE NEW CHARACTER"
            character = new_character_from_form()
        elif save_character_as == "temp":
            print "CREATE NEW CHARACTER, TEMP"
            raise NotImplementedError
        else:
            abort(400)
    elif new_or_saved_character == "saved":
        if edit_character:
            if save_character_as == "update":
                print "UPDATE EXISTING CHARACTER"
                # Update an existing character's details.
                try:
                    character_id = int(request.form["character_id"])
                except ValueError:
                    abort(400)
                character = save_character_from_form(character_id)
            elif save_character_as == "new":
                print "CREATE NEW CHARACTER"
                character = new_character_from_form()
            elif save_character_as == "temp":
                print "CREATE NEW CHARACTER, TEMP"
                raise NotImplementedError
            else:
                abort(400)
        else:
            print "USE EXISTING CHARACTER UNMODIFIED"
            # Use an existing character unmodified.
            try:
                character = g.db.query(UserCharacter).filter(and_(
                    UserCharacter.id == int(request.form["character_id"]),
                    UserCharacter.user_id == g.user.id,
                )).one()
            except ValueError:
                abort(400)
            except NoResultFound:
                abort(404)
    else:
        abort(400)

    scenario = request.form["scenario"].strip()
    prompt = request.form["prompt"].strip()

    # At least one of prompt or scenario must be filled in.
    if len(scenario) == 0 and len(prompt) == 0:
        abort(400)

    new_request = Request(
        user=g.user,
        status="draft" if "draft" in request.form else "posted",
        user_character=character,
        scenario=scenario,
        prompt=prompt,
    )
    new_request.tags = _tags_from_form(request.form)
    g.db.add(new_request)

    return redirect(url_for("rp_your_request_list"))


@use_db
@login_required
def answer_request(request_id):

    try:
        search_request = g.db.query(Request).filter(
            Request.id == request_id,
        ).options(
            joinedload(Request.user),
            joinedload(Request.user_character),
        ).one()
    except NoResultFound:
        abort(404)

    if search_request.status != "posted" or search_request.user == g.user:
        abort(404)

    new_chat = RequestedChat(url=str(uuid4()).replace("-", ""))
    g.db.add(new_chat)
    g.db.flush()

    if search_request.user_character is not None:
        new_chat_user = ChatUser.from_character(
            search_request.user_character,
            chat_id=new_chat.id,
        )
    else:
        new_chat_user = ChatUser.from_user(
            search_request.user,
            chat_id=new_chat.id,
        )
    g.db.add(new_chat_user)

    if len(search_request.scenario) > 0:
        g.db.add(Message(
            chat_id=new_chat.id,
            type="search_info",
            alias="Scenario",
            text=search_request.scenario,
        ))

    if len(search_request.prompt) > 0:
        g.db.add(Message(
            chat_id=new_chat.id,
            user_id=new_chat_user.user_id,
            type="ic",
            color=new_chat_user.color,
            alias=new_chat_user.alias,
            name=new_chat_user.name,
            text=search_request.prompt,
        ))

    return redirect(url_for("rp_chat", url=new_chat.url))


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

    tags_by_type = search_request.tags_by_type()

    try:
        search_request_maturity = tags_by_type["maturity"][0]["name"]
    except IndexError:
        search_request_maturity = None

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
        selected_character=selected_character,
        error=error,
    )


@use_db
@login_required
def edit_request_get(request_id):
    return _edit_request_form(_own_request_query(request_id))


@use_db
@login_required
def edit_request_post(request_id):

    search_request = _own_request_query(request_id)

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
    except (KeyError, ValueError, NoResultFound):
        character = None

    search_request.scenario = scenario
    search_request.prompt = prompt
    search_request.user_character = character

    g.db.query(RequestTag).filter(RequestTag.request_id == search_request.id).delete()

    search_request.tags += _tags_from_form(request.form)

    if "draft" in request.form:
        search_request.status = "draft"
    elif search_request.status != "posted":
        search_request.status = "posted"
        # Bump the date if the request is being re-posted.
        search_request.posted = datetime.datetime.now()

    return redirect(url_for("rp_edit_request_get", request_id=search_request.id))


@use_db
@login_required
def delete_request_get(request_id):
    return render_template(
        "rp/request_search/delete_request.html",
        search_request=_own_request_query(request_id),
    )


@use_db
@login_required
def delete_request_post(request_id):
    search_request = _own_request_query(request_id)
    g.db.query(RequestTag).filter(RequestTag.request_id == search_request.id).delete()
    g.db.query(Request).filter(Request.id == search_request.id).delete()
    g.db.commit()
    return redirect(url_for("rp_your_request_list"))

