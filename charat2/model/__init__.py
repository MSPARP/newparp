import datetime
import json
import os
import time

from pytz import timezone, utc
from sqlalchemy import and_, create_engine
from sqlalchemy.schema import Index
from sqlalchemy.orm import (
    backref,
    relation,
    scoped_session,
    sessionmaker,
    with_polymorphic,
)
# Sorry SQLiters, this just ain't gonna work.
from sqlalchemy.dialects.postgresql import ARRAY, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    func,
    Column,
    ForeignKey,
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Unicode,
    UnicodeText,
    UniqueConstraint,
)

engine = create_engine(
    os.environ["POSTGRES_URL"],
    convert_unicode=True,
    pool_recycle=3600,
    echo="ECHO" in os.environ,
)

sm = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

base_session = scoped_session(sm)

Base = declarative_base()
Base.query = base_session.query_property()


def now():
    return datetime.datetime.now()


case_options = {
    u"alt-lines": "ALTERNATING lines",
    u"alternating": "AlTeRnAtInG",
    u"inverted": "iNVERTED",
    u"lower": u"lower case",
    u"normal": u"Normal",
    u"title": u"Title Case",
    u"upper": u"UPPER CASE",
    u"proper": u"Proper grammar",
    u"first-letter": u"First letter caps",
}

case_options_enum = Enum(*case_options.keys(), name=u"case")


# 1. Classes


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    # Username must be alphanumeric.
    username = Column(String(50), nullable=False)

    # Bcrypt hash.
    password = Column(String(60), nullable=False)
    secret_question = Column(Unicode(50), nullable=False)
    secret_answer = Column(String(60), nullable=False)

    email_address = Column(String(100))

    group = Column(Enum(
        u"guest",
        u"active",
        u"admin",
        u"banned",
        name=u"users_group",
    ), nullable=False, default=u"guest")

    created = Column(DateTime(), nullable=False, default=now)
    last_online = Column(DateTime(), nullable=False, default=now)
    last_ip = Column(INET, nullable=False)

    # Default character for entering group chats
    default_character_id = Column(Integer, ForeignKey(
        "characters.id",
        name="users_default_character_fkey",
        use_alter=True,
    ))

    last_search_mode = Column(
        Enum(u"roulette", u"search", name="user_last_search_mode"),
        nullable=False, default=u"roulette",
    )

    # Character info for searching
    roulette_search_character_id = Column(Integer, ForeignKey("search_characters.id"), nullable=False, default=1)
    roulette_character_id = Column(Integer, ForeignKey(
        "characters.id",
        name="users_roulette_character_fkey",
        use_alter=True,
    ))
    search_character_id = Column(Integer, ForeignKey("search_characters.id"), nullable=False, default=1)
    name = Column(Unicode(50), nullable=False, default=u"anonymous")
    acronym = Column(Unicode(15), nullable=False, default=u"??")
    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")
    quirk_prefix = Column(Unicode(100), nullable=False, default=u"")
    quirk_suffix = Column(Unicode(100), nullable=False, default=u"")
    case = Column(case_options_enum, nullable=False, default=u"normal")
    replacements = Column(UnicodeText, nullable=False, default=u"[]")
    regexes = Column(UnicodeText, nullable=False, default=u"[]")
    search_style = Column(
        Enum(u"script", u"paragraph", u"either", name="user_search_style"),
        nullable=False, default=u"script",
    )
    search_level = Column(
        Enum(u"sfw", u"nsfw", name="user_search_level"),
        nullable=False, default=u"sfw",
    )

    # psycopg2 doesn't handle arrays of custom types by default, so we just use strings here.
    group_chat_styles = Column(ARRAY(Unicode(50)), nullable=False, default=[u"script"])
    group_chat_levels = Column(ARRAY(Unicode(50)), nullable=False, default=[u"sfw"])

    confirm_disconnect = Column(Boolean, nullable=False, default=True)
    desktop_notifications = Column(Boolean, nullable=False, default=False)
    show_system_messages = Column(Boolean, nullable=False, default=True)
    show_bbcode = Column(Boolean, nullable=False, default=True)
    show_preview = Column(Boolean, nullable=False, default=True)
    typing_notifications = Column(Boolean, nullable=False, default=True)

    timezone = Column(Unicode(255))

    def __repr__(self):
        return "<User #%s: %s>" % (self.id, self.username)

    def localize_time(self, input_datetime):
        utc_datetime = utc.localize(input_datetime)
        if self.timezone is None:
            return utc_datetime
        return utc_datetime.astimezone(timezone(self.timezone))

    def to_dict(self, include_options=False):
        ud = {
            "id": self.id,
            "username": self.username,
            "group": self.group,
            "created": time.mktime(self.created.timetuple()),
            "last_online": time.mktime(self.last_online.timetuple()),
            "name": self.name,
            "acronym": self.acronym,
            "color": self.color,
            "search_style": self.search_style,
            "search_level": self.search_level,
        }
        if include_options:
            ud["default_character"] = self.default_character.to_dict() if self.default_character is not None else None
            ud["search_character"] = self.search_character.to_dict()
            ud["quirk_prefix"] = self.quirk_prefix
            ud["quirk_suffix"] = self.quirk_suffix
            ud["case"] = self.case
            ud["replacements"] = json.loads(self.replacements)
            ud["regexes"] = json.loads(self.regexes)
        return ud


class Block(Base):
    __tablename__ = "blocks"
    blocking_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    blocked_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    created = Column(DateTime(), nullable=False, default=now)
    reason = Column(UnicodeText)

    def __repr__(self):
        return "<Block: %s blocked %s>" % (self.blocking_user, self.blocked_user)


class Character(Base):

    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(Unicode(50), nullable=False)
    search_character_id = Column(Integer, ForeignKey("search_characters.id"), nullable=False, default=1)
    shortcut = Column(Unicode(15))

    name = Column(Unicode(50), nullable=False, default=u"anonymous")
    acronym = Column(Unicode(15), nullable=False, default=u"??")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")

    quirk_prefix = Column(Unicode(100), nullable=False, default=u"")
    quirk_suffix = Column(Unicode(100), nullable=False, default=u"")

    case = Column(case_options_enum, nullable=False, default=u"normal")

    replacements = Column(UnicodeText, nullable=False, default=u"[]")
    regexes = Column(UnicodeText, nullable=False, default=u"[]")

    def __repr__(self):
        return "<Character #%s: %s>" % (self.id, self.title.encode("utf8"))

    def tags_by_type(self):
        tags = { "fandom": [], "character": [], "gender": [] }
        for character_tag in self.tags:
            # Characters should only have fandom, character and gender tags,
            # so ignore any others.
            if character_tag.tag.type not in tags:
                continue
            tags[character_tag.tag.type].append({
                "type": character_tag.tag.type,
                "name": character_tag.tag.name,
                "alias": character_tag.alias,
            })
        return tags

    def to_dict(self, include_default=False, include_options=False):
        ucd = {
            "id": self.id,
            "title": self.title,
            "search_character_id": self.search_character_id,
            "shortcut": self.shortcut,
            "name": self.name,
            "acronym": self.acronym,
            "color": self.color,
        }
        if include_default:
            ucd["default"] = self.id == self.user.default_character_id
        if include_options:
            ucd["quirk_prefix"] = self.quirk_prefix
            ucd["quirk_suffix"] = self.quirk_suffix
            ucd["case"] = self.case
            ucd["replacements"] = json.loads(self.replacements)
            ucd["regexes"] = json.loads(self.regexes)
            ucd["tags"] = self.tags_by_type()
            ucd["search_character"] = self.search_character.to_dict()
        return ucd


class SearchCharacter(Base):

    __tablename__ = "search_characters"

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(50), nullable=False)
    group_id = Column(Integer, ForeignKey("search_character_groups.id"), nullable=False)
    order = Column(Integer, nullable=False)

    name = Column(Unicode(50), nullable=False, default=u"anonymous")
    acronym = Column(Unicode(15), nullable=False, default=u"??")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")

    quirk_prefix = Column(Unicode(100), nullable=False, default=u"")
    quirk_suffix = Column(Unicode(100), nullable=False, default=u"")

    case = Column(case_options_enum, nullable=False, default=u"normal")

    replacements = Column(UnicodeText, nullable=False, default=u"[]")
    regexes = Column(UnicodeText, nullable=False, default=u"[]")

    text_preview = Column(UnicodeText, nullable=False, default=u"oh god how did this get here I am not good with computer")

    def __repr__(self):
        return "<SearchCharacter #%s: %s>" % (self.id, self.title.encode("utf8"))

    def to_dict(self, include_options=False):
        ucd = {
            "id": self.id,
            "title": self.title,
            "name": self.name,
            "acronym": self.acronym,
            "color": self.color,
            "text_preview": self.text_preview,
        }
        if include_options:
            ucd["quirk_prefix"] = self.quirk_prefix
            ucd["quirk_suffix"] = self.quirk_suffix
            ucd["case"] = self.case
            ucd["replacements"] = json.loads(self.replacements)
            ucd["regexes"] = json.loads(self.regexes)
        return ucd


class SearchCharacterGroup(Base):
    __tablename__ = "search_character_groups"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)
    order = Column(Integer, nullable=False)

    def __repr__(self):
        return "<SearchCharacterGroup #%s: %s>" % (self.id, self.name.encode("utf8"))


class SearchCharacterChoice(Base):
    __tablename__ = "search_character_choices"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    search_character_id = Column(Integer, ForeignKey("search_characters.id"), primary_key=True)

    def __repr__(self):
        return "<SearchCharacterChoice: %s chose %s>" % (self.user, self.search_character)


class Chat(Base):

    __tablename__ = "chats"
    __mapper_args__ = { "polymorphic_on": "type" }

    id = Column(Integer, primary_key=True)

    # URL must be alphanumeric. It must normally be capped to 50 characters,
    # but sub-chats are prefixed with the parent URL and a slash, so we need
    # 101 characters to fit 50 characters in each half.
    url = Column(String(101), unique=True)

    # Group chats allow people to enter in accordance with the publicity
    # options in the group_chats table, and can have any URL.
    # PM chats only allow two people to enter and have urls of the form
    # `pm/<user id 1>/<user id 2>`, with the 2 user IDs in alphabetical
    # order.
    # Searched chats allow anyone to enter and have randomly generated URLs.
    type = Column(Enum(
        u"group",
        u"pm",
        u"requested",
        u"roulette",
        u"searched",
        name=u"chats_type",
    ), nullable=False, default=u"group")

    created = Column(DateTime(), nullable=False, default=now)

    # Last message time should only update when users send messages, not system
    # messages.
    last_message = Column(DateTime(), nullable=False, default=now)

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "type": self.type,
        }


class GroupChat(Chat):

    __tablename__ = "group_chats"

    id = Column(Integer, ForeignKey("chats.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "group",
        "inherit_condition": id == Chat.id,
    }

    title = Column(Unicode(50), nullable=False, default=u"")
    topic = Column(UnicodeText, nullable=False, default=u"")
    description = Column(UnicodeText, nullable=False, default=u"")
    rules = Column(UnicodeText, nullable=False, default=u"")

    autosilence = Column(Boolean, nullable=False, default=False)

    style = Column(Enum(
        u"script",
        u"paragraph",
        u"either",
        name=u"group_chats_style",
    ), nullable=False, default=u"script")
    level = Column(Enum(
        u"sfw",
        u"nsfw",
        u"nsfw-extreme",
        name=u"group_chats_level",
    ), nullable=False, default=u"sfw")

    publicity = Column(Enum(
        u"listed",
        u"unlisted",
        u"pinned",
        u"admin_only",
        u"private",
        name=u"group_chats_publicity",
    ), nullable=False, default=u"unlisted")

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("chats.id"))

    def __repr__(self):
        return "<GroupChat #%s: %s>" % (self.id, self.url)

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "type": self.type,
            "title": self.title,
            "topic": self.topic,
            "description": self.description,
            "rules": self.rules,
            "autosilence": self.autosilence,
            "style": self.style,
            "level": self.level,
            "publicity": self.publicity,
        }


class PMChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "pm" }

    def __repr__(self):
        return "<PMChat #%s: %s>" % (self.id, self.url)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
        }


class RequestedChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "requested" }

    def __repr__(self):
        return "<RequestedChat #%s: %s>" % (self.id, self.url)


class RouletteChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "roulette" }

    def __repr__(self):
        return "<RouletteChat #%s: %s>" % (self.id, self.url)


class SearchedChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "searched" }

    def __repr__(self):
        return "<SearchedChat #%s: %s>" % (self.id, self.url)


AnyChat = with_polymorphic(Chat, [GroupChat, PMChat, RequestedChat, RouletteChat, SearchedChat])


class ChatUser(Base):

    __tablename__ = "chat_users"

    chat_id = Column(Integer, ForeignKey("chats.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    number = Column(Integer, nullable=False)

    subscribed = Column(Boolean, nullable=False, default=True)

    last_online = Column(DateTime(), nullable=False, default=now)

    # Ignored if the user is an admin or the chat's creator.
    group = Column(Enum(
        u"mod3",
        u"mod2",
        u"mod1",
        u"silent",
        u"user",
        name=u"chat_users_group",
    ), nullable=False, default=u"user")

    name = Column(Unicode(50), nullable=False, default=u"anonymous")
    acronym = Column(Unicode(15), nullable=False, default=u"??")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")

    quirk_prefix = Column(Unicode(100), nullable=False, default=u"")
    quirk_suffix = Column(Unicode(100), nullable=False, default=u"")

    case = Column(case_options_enum, nullable=False, default=u"normal")

    replacements = Column(UnicodeText, nullable=False, default=u"[]")
    regexes = Column(UnicodeText, nullable=False, default=u"[]")

    confirm_disconnect = Column(Boolean, nullable=False, default=True)
    desktop_notifications = Column(Boolean, nullable=False, default=False)
    show_system_messages = Column(Boolean, nullable=False, default=True)
    show_bbcode = Column(Boolean, nullable=False, default=True)
    show_preview = Column(Boolean, nullable=False, default=True)
    typing_notifications = Column(Boolean, nullable=False, default=True)

    # No joins or filtering here so these don't need to be foreign keys.
    highlighted_numbers = Column(ARRAY(Integer), nullable=False, default=lambda: [])
    ignored_numbers = Column(ARRAY(Integer), nullable=False, default=lambda: [])

    draft = Column(UnicodeText)

    def __repr__(self):
        return "<ChatUser: %s in %s>" % (self.user, self.chat)

    @classmethod
    def from_character(cls, character, **kwargs):
        # Create a ChatUser using a Character and their user to determine the
        # default values.
        return cls(
            user_id=character.user.id,
            name=character.name,
            acronym=character.acronym,
            color=character.color,
            quirk_prefix=character.quirk_prefix,
            quirk_suffix=character.quirk_suffix,
            case=character.case,
            replacements=character.replacements,
            regexes=character.regexes,
            confirm_disconnect=user.confirm_disconnect,
            desktop_notifications=user.desktop_notifications,
            show_system_messages=user.show_system_messages,
            show_bbcode=user.show_bbcode,
            show_preview=user.show_preview,
            typing_notifications=user.typing_notifications,
            **kwargs
        )

    @classmethod
    def from_user(cls, user, **kwargs):
        # Create a ChatUser using a User to determine their settings.
        # Also inherit their default character if they have one and there
        # isn't one in the arguments.
        if user.default_character is not None and "name" not in kwargs:
            dc = user.default_character
            return cls(
                user_id=user.id,
                name=dc.name,
                acronym=dc.acronym,
                color=dc.color,
                quirk_prefix=dc.quirk_prefix,
                quirk_suffix=dc.quirk_suffix,
                case=dc.case,
                replacements=dc.replacements,
                regexes=dc.regexes,
                confirm_disconnect=user.confirm_disconnect,
                desktop_notifications=user.desktop_notifications,
                show_system_messages=user.show_system_messages,
                show_bbcode=user.show_bbcode,
                show_preview=user.show_preview,
                typing_notifications=user.typing_notifications,
                **kwargs
            )
        return cls(
            user_id=user.id,
            confirm_disconnect=user.confirm_disconnect,
            desktop_notifications=user.desktop_notifications,
            show_system_messages=user.show_system_messages,
            show_bbcode=user.show_bbcode,
            show_preview=user.show_preview,
            typing_notifications=user.typing_notifications,
            **kwargs
        )

    # Group changes and user actions can only be performed on people of the
    # same group as yourself and lower. To make this easier to check, we store
    # a numeric value for each rank so we can do a simple less-than-or-equal-to
    # comparison.
    group_ranks = {
        "admin": float("inf"),
        "creator": float("inf"),
        "mod3": 3,
        "mod2": 2,
        "mod1": 1,
        "user": 0,
        "silent": -1,
    }

    # Minimum ranks for actions.
    action_ranks = {
        "invite": 3,
        "ban": 3,
        "kick": 2,
        # XXX different ranks for each flag?
        "set_flag": 1,
        "set_group": 1,
        "set_topic": 1,
        "set_info": 1,
    }

    @property
    def computed_group(self):
        # Group is overridden by chat creator and user status.
        # Needs joinedload whenever we're getting these.
        if self.user.group == "admin":
            return "admin"
        if self.chat.type == "group" and self.chat.creator == self.user:
            return "creator"
        return self.group

    @property
    def computed_rank(self):
        return self.group_ranks[self.computed_group]

    def can(self, action):
        return self.group_ranks[self.computed_group] >= self.action_ranks[action]

    def to_dict(self, include_user=False, include_options=False):
        ucd = {
            "character": {
                "name": self.name,
                "acronym": self.acronym,
                "color": self.color,
            },
            "meta": {
                "number": self.number,
                # Group is overridden by chat creator and user status.
                # Needs joinedload whenever we're getting these.
                "group": self.computed_group,
            },
        }
        if include_options:
            ucd["character"]["quirk_prefix"] = self.quirk_prefix
            ucd["character"]["quirk_suffix"] = self.quirk_suffix
            ucd["character"]["case"] = self.case
            ucd["character"]["replacements"] = json.loads(self.replacements)
            ucd["character"]["regexes"] = json.loads(self.regexes)
            ucd["meta"]["subscribed"] = self.subscribed
            ucd["meta"]["confirm_disconnect"] = self.confirm_disconnect
            ucd["meta"]["desktop_notifications"] = self.desktop_notifications
            ucd["meta"]["show_system_messages"] = self.show_system_messages
            ucd["meta"]["show_bbcode"] = self.show_bbcode
            ucd["meta"]["show_preview"] = self.show_preview
            ucd["meta"]["typing_notifications"] = self.typing_notifications
            ucd["meta"]["highlighted_numbers"] = self.highlighted_numbers
            ucd["meta"]["ignored_numbers"] = self.ignored_numbers
            ucd["draft"] = self.draft or ""
        if include_user:
            ucd["user"] = {
                "user_id": self.user.id,
                "username": self.user.username,
            }
        return ucd


class Message(Base):

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)

    # Can be null because system messages aren't associated with a user.
    user_id = Column(Integer, ForeignKey("users.id"))

    posted = Column(DateTime(), nullable=False, default=now)

    # XXX CONSIDER SPLITTING SYSTEM INTO USER_CHANGE, META_CHANGE ETC.
    type = Column(Enum(
        u"ic",
        u"ooc",
        u"me",
        u"join",
        u"disconnect",
        u"timeout",
        u"user_info",
        u"user_group",
        u"user_action",
        u"chat_meta",
        u"search_info",
        u"spamless",
        name=u"messages_type",
    ), nullable=False, default=u"ic")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")

    acronym = Column(Unicode(15), nullable=False, default=u"")

    name = Column(Unicode(50), nullable=False, default=u"")

    text = Column(UnicodeText, nullable=False)

    spam_flag = Column(Unicode(15))

    def __repr__(self):
        if len(self.text) < 50:
            preview = self.text
        else:
            preview = self.text[:47] + "..."
        return "<Message #%s: \"%s\">" % (self.id, preview.encode("utf8"))

    def to_dict(self, include_user=False, include_spam_flag=True):
        md = {
            "id": self.id,
            "user_number": self.chat_user.number if self.chat_user is not None else None,
            "posted": time.mktime(self.posted.timetuple()),
            "type": self.type,
            "color": self.color,
            "acronym": self.acronym,
            "name": self.name,
            "text": self.text,
        }
        if include_user:
            md["user"] = {
                "id": self.user.id,
                "username": self.user.username,
            } if self.user is not None else None
        if include_spam_flag:
            md["spam_flag"] = self.spam_flag
        return md


class Invite(Base):

    __tablename__ = "invites"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), primary_key=True)

    creator_id = Column(Integer, ForeignKey("users.id"))
    created = Column(DateTime(), nullable=False, default=now)

    def __repr__(self):
        return "<Invite: %s to %s>" % (self.user, self.chat)

    def to_dict(self):
        return {
            "invited": self.chat_user.to_dict(include_user=True),
            "creator": self.creator_chat_user.to_dict(include_user=True),
        }


class Ban(Base):

    __tablename__ = "bans"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), primary_key=True)

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created = Column(DateTime(), nullable=False, default=now)
    expires = Column(DateTime())

    reason = Column(UnicodeText)

    def __repr__(self):
        return "<Ban: %s from %s>" % (self.user, self.chat)


class Request(Base):

    __tablename__ = "requests"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    status = Column(Enum(
        u"draft",
        u"posted",
        name=u"requests_status",
    ), nullable=False, default=u"draft")

    posted = Column(DateTime(), nullable=False, default=now)

    character_id = Column(Integer, ForeignKey("characters.id"))

    name = Column(Unicode(50), nullable=False, default=u"anonymous")
    acronym = Column(Unicode(15), nullable=False, default=u"??")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")

    quirk_prefix = Column(Unicode(100), nullable=False, default=u"")
    quirk_suffix = Column(Unicode(100), nullable=False, default=u"")

    case = Column(case_options_enum, nullable=False, default=u"normal")

    replacements = Column(UnicodeText, nullable=False, default=u"[]")
    regexes = Column(UnicodeText, nullable=False, default=u"[]")

    scenario = Column(UnicodeText, nullable=False, default=u"")
    prompt = Column(UnicodeText, nullable=False, default=u"")

    def tags_by_type(self):
        tags = { _: [] for _ in Tag.type_options }
        for request_tag in self.tags:
            tags[request_tag.tag.type].append({
                "type": request_tag.tag.type,
                "name": request_tag.tag.name,
                "alias": request_tag.alias,
            })
        return tags

    def to_dict(self, user=None):
        rd = {
            "id": self.id,
            "status": self.status,
            "posted": time.mktime(self.posted.timetuple()),
            "tags": self.tags_by_type(),
            "name": self.name,
            "acronym": self.acronym,
            "color": self.color,
            "scenario": self.scenario,
            "prompt": self.prompt,
        }
        if user is not None:
            rd["yours"] = user.id == self.user_id
            if rd["yours"]:
                rd["quirk_prefix"] = self.quirk_prefix
                rd["quirk_suffix"] = self.quirk_suffix
                rd["case"] = self.case
                rd["replacements"] = json.loads(self.replacements)
                rd["regexes"] = json.loads(self.regexes)
        return rd


class CharacterTag(Base):

    __tablename__ = "character_tags"

    character_id = Column(Integer, ForeignKey("characters.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

    alias = Column(Unicode(50))


class RequestTag(Base):

    __tablename__ = "request_tags"

    request_id = Column(Integer, ForeignKey("requests.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

    alias = Column(Unicode(50))


class Tag(Base):

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)

    type_options = {
        u"maturity",
        u"trigger",
        u"type",
        u"fandom",
        u"fandom_wanted",
        u"character",
        u"character_wanted",
        u"gender",
        u"gender_wanted",
        u"misc",
    }

    # List to preserve order.
    maturity_names = ["general", "teen", "mature", "explicit"]
    type_names = ["fluff", "plot-driven", "sexual", "shippy", "violent"]

    type = Column(Enum(*type_options, name=u"tags_type"), nullable=False, default=u"misc")
    name = Column(Unicode(50), nullable=False)

    synonym_id = Column(Integer, ForeignKey("tags.id"))


class AdminLogEntry(Base):

    __tablename__ = "admin_log_entries"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(), nullable=False, default=now)
    action_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Unicode(50), nullable=False)
    description = Column(UnicodeText)
    affected_user_id = Column(Integer, ForeignKey("users.id"))
    chat_id = Column(Integer, ForeignKey("chats.id"))

    def to_dict(self):
        return {
            "id": self.id,
            "date": time.mktime(self.date.timetuple()),
            "action_user": self.action_user.to_dict(),
            "type": self.type,
            "description": self.description,
            "affected_user": self.affected_user.to_dict() if self.affected_user is not None else None,
            "chat": self.chat.to_dict() if self.chat is not None else None,
        }


class IPBan(Base):
    __tablename__ = "ip_bans"
    address = Column(INET, primary_key=True)
    date = Column(DateTime(), nullable=False, default=now)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Unicode(255), nullable=False)

    def __repr__(self):
        return "<IPBan: %s>" % self.address

    def to_dict(self):
        return {
            "address": self.address,
            "date": time.mktime(self.date.timetuple()),
            "creator": self.creator.to_dict(),
            "reason": self.reason,
        }


# 2. Indexes


# Index to make usernames case insensitively unique.
Index("users_username", func.lower(User.username), unique=True)

# Index for user characters.
Index("characters_user_id", Character.user_id)

# Index to make generating the public chat list easier.
# This is a partial index, a feature only supported by Postgres, so I don't
# know what will happen if you try to run this on anything else.
Index(
    "group_chats_publicity_listed",
    GroupChat.publicity,
    postgresql_where=GroupChat.publicity.in_((u"listed", u"pinned")),
)

# Index for your chats list.
Index("chat_users_user_id_subscribed", ChatUser.user_id, ChatUser.subscribed)

# Index for user number lookup.
Index("chat_users_number_unique", ChatUser.chat_id, ChatUser.number, unique=True)

# Index to make log rendering easier.
Index("messages_chat_id", Message.chat_id, Message.posted)

# XXX indexes on requests table
# index by user id for your requests?

# Index for searching characters by tag.
Index("character_tags_tag_id", CharacterTag.tag_id)

# Index for searching requests by tag.
Index("request_tags_tag_id", RequestTag.tag_id)

# Index to make tag type/name combo unique.
Index("tags_type_name", Tag.type, Tag.name, unique=True)


# 3. Relationships

User.default_character = relation(
    Character,
    primaryjoin=User.default_character_id == Character.id,
)
User.characters = relation(
    Character,
    primaryjoin=User.id == Character.user_id,
    backref="user",
)
User.search_character = relation(SearchCharacter, foreign_keys=User.search_character_id)
User.roulette_search_character = relation(SearchCharacter, foreign_keys=User.roulette_search_character_id)
User.roulette_character = relation(Character, foreign_keys=User.roulette_character_id)

Block.blocking_user = relation(User, primaryjoin=Block.blocking_user_id == User.id)
Block.blocked_user = relation(User, primaryjoin=Block.blocked_user_id == User.id)

Character.search_character = relation(SearchCharacter, backref="characters")
Character.tags = relation(CharacterTag, backref="character", order_by=CharacterTag.alias)

SearchCharacterGroup.characters = relation(SearchCharacter, backref="group", order_by=SearchCharacter.order)

SearchCharacterChoice.user = relation(User, backref="search_character_choices")
SearchCharacterChoice.character = relation(SearchCharacter, backref="users")

GroupChat.creator = relation(User, backref="created_chats")
GroupChat.parent = relation(
    Chat,
    backref="children",
    primaryjoin=GroupChat.parent_id == Chat.id,
)

ChatUser.user = relation(User, backref="chats")
ChatUser.chat = relation(Chat, backref="users")

Message.chat = relation(Chat)
Message.user = relation(User)
Message.chat_user = relation(
    ChatUser,
    primaryjoin=and_(
        Message.user_id != None,
        Message.chat_id == ChatUser.chat_id,
        Message.user_id == ChatUser.user_id,
    ),
    foreign_keys=[Message.chat_id, Message.user_id],
)

Invite.chat = relation(Chat, backref="invites")
Invite.user = relation(
    User,
    backref="invites",
    primaryjoin=Invite.user_id == User.id,
)
Invite.chat_user = relation(
    ChatUser,
    primaryjoin=and_(
        Invite.chat_id == ChatUser.chat_id,
        Invite.user_id == ChatUser.user_id,
    ),
    foreign_keys=[Invite.chat_id, Invite.user_id],
    backref=backref("invite", uselist=False),
)
Invite.creator = relation(
    User,
    backref="invites_created",
    primaryjoin=Invite.creator_id == User.id,
)
Invite.creator_chat_user = relation(
    ChatUser,
    primaryjoin=and_(
        Invite.chat_id == ChatUser.chat_id,
        Invite.creator_id == ChatUser.user_id,
    ),
    foreign_keys=[Invite.chat_id, Invite.creator_id],
)

Ban.chat = relation(Chat, backref="bans")
Ban.user = relation(
    User,
    backref="bans",
    primaryjoin=Ban.user_id == User.id,
)
Ban.chat_user = relation(
    ChatUser,
    primaryjoin=and_(
        Ban.chat_id == ChatUser.chat_id,
        Ban.user_id == ChatUser.user_id,
    ),
    foreign_keys=[Ban.chat_id, Ban.user_id],
    backref=backref("ban", uselist=False),
)
Ban.creator = relation(
    User,
    backref="bans_created",
    primaryjoin=Ban.creator_id == User.id,
)
Ban.creator_chat_user = relation(
    ChatUser,
    primaryjoin=and_(
        Ban.chat_id == ChatUser.chat_id,
        Ban.creator_id == ChatUser.user_id,
    ),
    foreign_keys=[Ban.chat_id, Ban.creator_id],
)

Request.user = relation(User, backref="requests")
Request.character = relation(Character, backref="requests")
Request.tags = relation(RequestTag, backref="request", order_by=RequestTag.alias)

Tag.characters = relation(CharacterTag, backref="tag")
Tag.requests = relation(RequestTag, backref="tag")
Tag.synonym_of = relation(Tag, backref="synonyms", remote_side=Tag.id)

AdminLogEntry.action_user = relation(User, backref="admin_actions", foreign_keys=AdminLogEntry.action_user_id)
AdminLogEntry.affected_user = relation(User, foreign_keys=AdminLogEntry.affected_user_id)
AdminLogEntry.chat = relation(Chat)

IPBan.creator = relation(User)

