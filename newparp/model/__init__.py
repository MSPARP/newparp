import datetime
import json
import os
import sys
import time

from bcrypt import gensalt, hashpw
from collections import OrderedDict
from enum import Enum
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
from sqlalchemy.pool import NullPool
# Sorry SQLiters, this just ain't gonna work.
from sqlalchemy.dialects.postgresql import ARRAY, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import (
    func,
    Column,
    ForeignKey,
    Boolean,
    DateTime,
    Enum as SQLAlchemyEnum,
    Integer,
    String,
    Unicode,
    UnicodeText,
    UniqueConstraint,
)

engine = create_engine(
    os.environ["POSTGRES_URL"],
    convert_unicode=True,
    echo="ECHO" in os.environ or "--debug" in sys.argv,
    poolclass=NullPool,
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


class AgeGroup(Enum):
    unknown  = "unknown"
    under_18 = "under_18"
    over_18  = "over_18"


case_options = OrderedDict([
    ("alt-lines",    "ALTERNATING lines"),
    ("alternating",  "AlTeRnAtInG"),
    ("inverted",     "iNVERTED"),
    ("lower",        "lower case"),
    ("normal",       "Normal"),
    ("title",        "Title Case"),
    ("upper",        "UPPER CASE"),
    ("proper",       "Proper grammar"),
    ("first-letter", "First letter caps"),
])

case_options_enum = SQLAlchemyEnum(*list(case_options.keys()), name="case")


# TODO make this an enum and use sqlalchemy-enum34
level_options = OrderedDict([
    ("sfw",          "SFW"),
    ("nsfwv",        "NSFW (violent)"),
    ("nsfws",        "NSFW (sexual)"),
    ("nsfw-extreme", "NSFW extreme"),
])

allowed_level_options = {
    AgeGroup.unknown:  {"sfw", "nsfwv"},
    AgeGroup.under_18: {"sfw", "nsfwv"},
    AgeGroup.over_18:  {"sfw", "nsfwv", "nsfws", "nsfw-extreme"},
}


# 1. Classes


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    # Username must be alphanumeric.
    username = Column(String(50), nullable=False)

    # Bcrypt hash.
    password = Column(String(60), nullable=False)
    secret_question = Column(Unicode(50))
    secret_answer = Column(String(60))

    date_of_birth = Column(DateTime())

    email_address = Column(String(100))
    email_verified = Column(Boolean, nullable=False, default=False)

    group = Column(SQLAlchemyEnum(
        "new",
        "active",
        "deactivated",
        "banned",
        name="users_group",
    ), nullable=False, default="guest")
    admin_tier_id = Column(Integer, ForeignKey("admin_tiers.id"))

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
        SQLAlchemyEnum("roulette", "search", name="user_last_search_mode"),
        nullable=False, default="roulette",
    )

    # Character info for searching
    roulette_search_character_id = Column(Integer, ForeignKey("search_characters.id"), nullable=False, default=1)
    roulette_character_id = Column(Integer, ForeignKey(
        "characters.id",
        name="users_roulette_character_fkey",
        use_alter=True,
    ))
    search_character_id = Column(Integer, ForeignKey("search_characters.id"), nullable=False, default=1)
    name = Column(Unicode(50), nullable=False, default="anonymous")
    acronym = Column(Unicode(15), nullable=False, default="??")
    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default="000000")
    quirk_prefix = Column(Unicode(2000), nullable=False, default="")
    quirk_suffix = Column(Unicode(2000), nullable=False, default="")
    case = Column(case_options_enum, nullable=False, default="normal")
    replacements = Column(UnicodeText, nullable=False, default="[]")
    regexes = Column(UnicodeText, nullable=False, default="[]")
    search_style = Column(
        SQLAlchemyEnum("script", "paragraph", "either", name="user_search_style"),
        nullable=False, default="script",
    )
    search_levels = Column(ARRAY(Unicode(50)),  nullable=False, default=["sfw"])
    search_filters = Column(ARRAY(Unicode(50)), nullable=False, default=[])
    search_age_restriction = Column(Boolean,    nullable=False, default=False)

    # psycopg2 doesn't handle arrays of custom types by default, so we just use strings here.
    group_chat_styles = Column(ARRAY(Unicode(50)), nullable=False, default=["script"])
    group_chat_levels = Column(ARRAY(Unicode(50)), nullable=False, default=["sfw"])

    confirm_disconnect = Column(Boolean, nullable=False, default=True)
    desktop_notifications = Column(Boolean, nullable=False, default=False)
    show_system_messages = Column(Boolean, nullable=False, default=True)
    show_user_numbers = Column(Boolean, nullable=False, default=True)
    show_bbcode = Column(Boolean, nullable=False, default=True)
    show_timestamps = Column(Boolean, nullable=False, default=False)
    show_preview = Column(Boolean, nullable=False, default=True)
    typing_notifications = Column(Boolean, nullable=False, default=True)
    enable_activity_indicator = Column(Boolean, nullable=False, default=True)

    timezone = Column(Unicode(255))
    theme = Column(Unicode(255))

    def __repr__(self):
        return "<User #%s: %s>" % (self.id, self.username)

    def set_password(self, password):
        if not password:
            raise ValueError("Password can't be blank.")
        self.password = hashpw(password.encode("utf8"), gensalt()).decode("utf8")

    def check_password(self, password):
        return hashpw(password.encode("utf8"), self.password.encode()).decode("utf8") == self.password

    @property
    def age(self):
        if self.date_of_birth is None:
            return None
        now = datetime.datetime.now()
        age = now.year - self.date_of_birth.year
        if self.date_of_birth.replace(year=now.year) > now:
            age -= 1
        return age

    @property
    def age_group(self):
        if self.date_of_birth is None:
            return AgeGroup.unknown
        return AgeGroup.over_18 if self.age >= 18 else AgeGroup.under_18

    @property
    def level_options(self):
        return allowed_level_options[self.age_group]

    @property
    def is_admin(self):
        return self.admin_tier_id is not None

    def has_permission(self, permission):
        if self.is_admin and permission in self.admin_tier.permissions:
            return True
        return False

    def localize_time(self, input_datetime):
        utc_datetime = utc.localize(input_datetime)
        if self.timezone is None:
            return utc_datetime
        return utc_datetime.astimezone(timezone(self.timezone))

    def to_dict(self, include_options=False):
        ud = {
            "id": self.id,
            "username": self.username,
            "email_address": self.email_address,
            "email_verified": self.email_verified,
            "group": self.group,
            "is_admin": self.is_admin,
            "created": time.mktime(self.created.timetuple()),
            "last_online": time.mktime(self.last_online.timetuple()),
            "name": self.name,
            "acronym": self.acronym,
            "color": self.color,
            "search_style": self.search_style,
            "search_levels": self.search_levels,
        }
        if include_options:
            ud["admin_tier"] = self.admin_tier.to_dict() if self.is_admin else None
            ud["default_character"] = self.default_character.to_dict() if self.default_character is not None else None
            ud["search_character"] = self.search_character.to_dict()
            ud["quirk_prefix"] = self.quirk_prefix
            ud["quirk_suffix"] = self.quirk_suffix
            ud["case"] = self.case
            ud["replacements"] = json.loads(self.replacements)
            ud["regexes"] = json.loads(self.regexes)
            ud["timezone"] = self.timezone
            ud["theme"] = self.theme
        return ud


class UserNote(Base):
    __tablename__ = "user_notes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created = Column(DateTime(), nullable=False, default=now)
    text = Column(UnicodeText, nullable=False)

    def to_dict(self):
        return {
            "user": {
                "id": self.user.id,
                "username": self.user.username,
            },
            "creator": {
                "id": self.creator.id,
                "username": self.creator.username,
            },
            "created": time.mktime(self.created.timetuple()),
            "text": self.text,
        }



class Block(Base):
    __tablename__ = "blocks"
    blocking_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    blocked_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    created = Column(DateTime(), nullable=False, default=now)
    reason = Column(UnicodeText)

    def __repr__(self):
        return "<Block: %s blocked %s>" % (self.blocking_user, self.blocked_user)

    def to_dict(self, include_users=False):
        bd = {
            "chat": self.chat.to_dict(),
            "created": time.mktime(self.created.timetuple()),
            "reason": self.reason,
        }
        if include_users:
            bd["blocking_user"] = self.blocking_user.to_dict()
            bd["blocked_user"] = self.blocked_user.to_dict()
        return bd


class Character(Base):

    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(Unicode(50), nullable=False, default="New character")
    search_character_id = Column(Integer, ForeignKey("search_characters.id"), nullable=False, default=1)
    shortcut = Column(Unicode(15))

    name = Column(Unicode(50), nullable=False, default="anonymous")
    acronym = Column(Unicode(15), nullable=False, default="??")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default="000000")

    quirk_prefix = Column(Unicode(2000), nullable=False, default="")
    quirk_suffix = Column(Unicode(2000), nullable=False, default="")

    case = Column(case_options_enum, nullable=False, default="normal")

    replacements = Column(UnicodeText, nullable=False, default="[]")
    regexes = Column(UnicodeText, nullable=False, default="[]")

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


class Fandom(Base):
    __tablename__ = "fandoms"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)

    def __repr__(self):
        return "<Fandom #%s: %s>" % (self.id, self.name.encode("utf8"))


class SearchCharacterGroup(Base):
    __tablename__ = "search_character_groups"
    id = Column(Integer, primary_key=True)
    fandom_id = Column(Integer, ForeignKey("fandoms.id"), nullable=False)
    name = Column(Unicode(50), nullable=False)
    order = Column(Integer, nullable=False)

    def __repr__(self):
        return "<SearchCharacterGroup #%s: %s>" % (self.id, self.name.encode("utf8"))


class SearchCharacter(Base):

    __tablename__ = "search_characters"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("search_character_groups.id"), nullable=False)
    title = Column(Unicode(50), nullable=False)
    order = Column(Integer, nullable=False)

    name = Column(Unicode(50), nullable=False, default="anonymous")
    acronym = Column(Unicode(15), nullable=False, default="??")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default="000000")

    quirk_prefix = Column(Unicode(2000), nullable=False, default="")
    quirk_suffix = Column(Unicode(2000), nullable=False, default="")

    case = Column(case_options_enum, nullable=False, default="normal")

    replacements = Column(UnicodeText, nullable=False, default="[]")
    regexes = Column(UnicodeText, nullable=False, default="[]")

    text_preview = Column(UnicodeText, nullable=False, default="oh god how did this get here I am not good with computer")

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
    type = Column(SQLAlchemyEnum(
        "group",
        "pm",
        "roulette",
        "searched",
        name="chats_type",
    ), nullable=False, default="group")

    created = Column(DateTime(), nullable=False, default=now)

    # Last message time should only update when users send messages, not system
    # messages.
    last_message = Column(DateTime(), nullable=False, default=now)

    # PM chats: "/pm/(username)"
    # Everything else: self.url
    def computed_url(self, *args, **kwargs):
        return self.url

    # Group chats: self.title
    # PM chats: "Messaging (username)"
    # Searched and roulette chats: same as the URL
    def computed_title(self, *args, **kwargs):
        return self.url

    def to_dict(self, *args, **kwargs):
        return {
            "id": self.id,
            "url": self.computed_url(*args, **kwargs),
            "type": self.type,
            "title": self.computed_title(*args, **kwargs),
        }


class GroupChat(Chat):

    __tablename__ = "group_chats"

    id = Column(Integer, ForeignKey("chats.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "group",
        "inherit_condition": id == Chat.id,
    }

    title = Column(Unicode(50), nullable=False, default="")
    topic = Column(UnicodeText, nullable=False, default="")
    description = Column(UnicodeText, nullable=False, default="")
    rules = Column(UnicodeText, nullable=False, default="")

    autosilence = Column(Boolean, nullable=False, default=False)

    style = Column(SQLAlchemyEnum(
        "script",
        "paragraph",
        "either",
        name="group_chats_style",
    ), nullable=False, default="script")
    level = Column(SQLAlchemyEnum(
        *level_options.keys(),
        name="group_chats_level",
    ), nullable=False, default="sfw")

    publicity = Column(SQLAlchemyEnum(
        "listed",
        "unlisted",
        "pinned",
        "admin_only",
        "private",
        name="group_chats_publicity",
    ), nullable=False, default="unlisted")

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("chats.id"))

    def __repr__(self):
        return "<GroupChat #%s: %s>" % (self.id, self.url)

    def computed_title(self, *args, **kwargs):
        return self.title

    def to_dict(self, *args, **kwargs):
        cd = super(GroupChat, self).to_dict(*args, **kwargs)
        cd["topic"] = self.topic
        cd["description"] = self.description
        cd["rules"] = self.rules
        cd["autosilence"] = self.autosilence
        cd["style"] = self.style
        cd["level"] = self.level
        cd["publicity"] = self.publicity
        return cd


class PMChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "pm" }

    def __repr__(self):
        return "<PMChat #%s: %s>" % (self.id, self.url)

    def computed_url(self, *args, **kwargs):
        if "pm_user" in kwargs and kwargs["pm_user"]:
            return "pm/" + kwargs["pm_user"].username
        return super(PMChat, self).computed_title(*args, **kwargs)

    def computed_title(self, *args, **kwargs):
        if "pm_user" in kwargs and kwargs["pm_user"]:
            return "Messaging " + kwargs["pm_user"].username
        return super(PMChat, self).computed_title(*args, **kwargs)


class RouletteChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "roulette" }

    def __repr__(self):
        return "<RouletteChat #%s: %s>" % (self.id, self.url)


class SearchedChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "searched" }

    def __repr__(self):
        return "<SearchedChat #%s: %s>" % (self.id, self.url)


AnyChat = with_polymorphic(Chat, [GroupChat, PMChat, RouletteChat, SearchedChat])


class LogMarker(Base):
    __tablename__ = "log_markers"
    chat_id = Column(Integer, ForeignKey("chats.id"), primary_key=True)
    type = Column(SQLAlchemyEnum(
        "page_with_system_messages",
        "page_without_system_messages",
        name="log_markers_type",
    ), primary_key=True, default="page_with_system_messages")
    number = Column(Integer, primary_key=True, autoincrement=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)


class ChatUser(Base):

    __tablename__ = "chat_users"

    chat_id = Column(Integer, ForeignKey("chats.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    number = Column(Integer, nullable=False)
    search_character_id = Column(Integer, ForeignKey("search_characters.id"), nullable=False, default=1)

    subscribed = Column(Boolean, nullable=False, default=False)
    title = Column(Unicode(50))
    notes = Column(UnicodeText)

    last_online = Column(DateTime(), nullable=False, default=now)

    # Ignored if the user is an admin or the chat's creator.
    group = Column(SQLAlchemyEnum(
        "mod3",
        "mod2",
        "mod1",
        "silent",
        "user",
        name="chat_users_group",
    ), nullable=False, default="user")

    name = Column(Unicode(50), nullable=False, default="anonymous")
    acronym = Column(Unicode(15), nullable=False, default="??")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default="000000")

    quirk_prefix = Column(Unicode(2000), nullable=False, default="")
    quirk_suffix = Column(Unicode(2000), nullable=False, default="")

    case = Column(case_options_enum, nullable=False, default="normal")

    replacements = Column(UnicodeText, nullable=False, default="[]")
    regexes = Column(UnicodeText, nullable=False, default="[]")

    confirm_disconnect = Column(Boolean, nullable=False, default=True)
    desktop_notifications = Column(Boolean, nullable=False, default=False)
    show_system_messages = Column(Boolean, nullable=False, default=True)
    show_user_numbers = Column(Boolean, nullable=False, default=True)
    show_bbcode = Column(Boolean, nullable=False, default=True)
    show_timestamps = Column(Boolean, nullable=False, default=False)
    show_preview = Column(Boolean, nullable=False, default=True)
    typing_notifications = Column(Boolean, nullable=False, default=True)
    enable_activity_indicator = Column(Boolean, nullable=False, default=True)

    theme = Column(Unicode(255))

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
            search_character_id=character.search_character_id,
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
            show_user_numbers=user.show_user_numbers,
            show_bbcode=user.show_bbcode,
            show_timestamps=user.show_timestamps,
            show_preview=user.show_preview,
            typing_notifications=user.typing_notifications,
            enable_activity_indicator=user.enable_activity_indicator,
            theme=user.theme,
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
                search_character_id=dc.search_character_id,
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
                show_user_numbers=user.show_user_numbers,
                show_bbcode=user.show_bbcode,
                show_timestamps=user.show_timestamps,
                show_preview=user.show_preview,
                typing_notifications=user.typing_notifications,
                enable_activity_indicator=user.enable_activity_indicator,
                theme=user.theme,
                **kwargs
            )
        return cls(
            user_id=user.id,
            confirm_disconnect=user.confirm_disconnect,
            desktop_notifications=user.desktop_notifications,
            show_system_messages=user.show_system_messages,
            show_user_numbers=user.show_user_numbers,
            show_bbcode=user.show_bbcode,
            show_timestamps=user.show_timestamps,
            show_preview=user.show_preview,
            typing_notifications=user.typing_notifications,
            enable_activity_indicator=user.enable_activity_indicator,
            theme=user.theme,
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
        if self.user.is_admin:
            return "admin"
        if self.chat.type == "group" and self.chat.creator == self.user:
            return "creator"
        return self.group

    @property
    def computed_rank(self):
        return self.group_ranks[self.computed_group]

    def can(self, action):
        return self.group_ranks[self.computed_group] >= self.action_ranks[action]

    def to_dict(self, include_user=False, include_options=False, include_title_and_notes=False):
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
            ucd["meta"]["show_user_numbers"] = self.show_user_numbers
            ucd["meta"]["show_bbcode"] = self.show_bbcode
            ucd["meta"]["show_timestamps"] = self.show_timestamps
            ucd["meta"]["show_preview"] = self.show_preview
            ucd["meta"]["typing_notifications"] = self.typing_notifications
            ucd["meta"]["enable_activity_indicator"] = self.enable_activity_indicator
            ucd["meta"]["theme"] = self.theme
            ucd["meta"]["highlighted_numbers"] = self.highlighted_numbers
            ucd["meta"]["ignored_numbers"] = self.ignored_numbers
            ucd["draft"] = self.draft or ""
        if include_options or include_title_and_notes:
            ucd["title"] = self.title or ""
            ucd["notes"] = self.notes or ""
        if include_user:
            ucd["user"] = {
                "user_id": self.user.id,
                "username": self.user.username,
            }
        return ucd


class Message(Base):

    MAX_LENGTH = 10000

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)

    # Can be null because system messages aren't associated with a user.
    user_id = Column(Integer, ForeignKey("users.id"))

    posted = Column(DateTime(), nullable=False, default=now)

    # XXX CONSIDER SPLITTING SYSTEM INTO USER_CHANGE, META_CHANGE ETC.
    type = Column(SQLAlchemyEnum(
        "ic",
        "ooc",
        "me",
        "join",
        "disconnect",
        "timeout",
        "user_info",
        "user_group",
        "user_action",
        "chat_meta",
        "search_info",
        "spamless",
        name="messages_type",
    ), nullable=False, default="ic")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default="000000")

    acronym = Column(Unicode(15), nullable=False, default="")

    name = Column(Unicode(50), nullable=False, default="")

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


class CharacterTag(Base):

    __tablename__ = "character_tags"

    character_id = Column(Integer, ForeignKey("characters.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

    alias = Column(Unicode(50))


class Tag(Base):

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)

    type_options = {
        "maturity",
        "trigger",
        "type",
        "fandom",
        "fandom_wanted",
        "character",
        "character_wanted",
        "gender",
        "gender_wanted",
        "misc",
    }

    # List to preserve order.
    maturity_names = ["general", "teen", "mature", "explicit"]
    type_names = ["fluff", "plot-driven", "sexual", "shippy", "violent"]

    type = Column(SQLAlchemyEnum(*type_options, name="tags_type"), nullable=False, default="misc")
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
    hidden = Column(Boolean, nullable=False, default=False, server_default="false")

    def __repr__(self):
        return "<IPBan: %s>" % self.address

    def to_dict(self):
        return {
            "address": self.address,
            "date": time.mktime(self.date.timetuple()),
            "creator": self.creator.to_dict(),
            "reason": self.reason,
        }


class EmailBan(Base):
    __tablename__ = "email_bans"
    id = Column(Integer, primary_key=True)
    pattern = Column(Unicode(255), nullable=False, unique=True)
    date = Column(DateTime(), nullable=False, default=now)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Unicode(255), nullable=False)

    def __repr__(self):
        return "<EmailBan: %s>" % self.address

    def to_dict(self):
        return {
            "id": self.id,
            "pattern": self.pattern,
            "date": time.mktime(self.date.timetuple()),
            "creator": self.creator.to_dict(),
            "reason": self.reason,
        }


class AdminTier(Base):
    __tablename__ = "admin_tiers"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), nullable=False)

    def __repr__(self):
        return "<AdminTier #%s: %s>" % (self.id, self.name)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "permissions": list(self.permissions),
        }


class AdminTierPermission(Base):
    __tablename__ = "admin_tier_permissions"
    admin_tier_id = Column(Integer, ForeignKey("admin_tiers.id"), primary_key=True)
    permission = Column(SQLAlchemyEnum(
        "search_characters",
        "announcements",
        "broadcast",
        "user_list",
        "reset_password",
        "permissions",
        "groups",
        "log",
        "spamless",
        "ip_bans",
        "email_bans",
        name="admin_tier_permissions_permission",
    ), primary_key=True)

    def __repr__(self):
        return "<AdminTierPermission: %s has %s>" % (self.admin_tier_id, self.permission)


spamless_filter_types = SQLAlchemyEnum(
    "banned_names",
    "blacklist",
    "warnlist",
    name="spamless_filter_types"
)


class SpamlessFilter(Base):
    __tablename__ = "spamless_filters"
    id = Column(Integer, primary_key=True)
    type = Column(spamless_filter_types, nullable=False)
    regex = Column(UnicodeText, nullable=False)
    points = Column(Integer, default=0)

    def __repr__(self):
        return "<SpamlessFilter: '%s'>" % (self.id, self.regex)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "regex": self.regex,
            "points": self.points,
        }


class SpamFlag(Base):
    __tablename__ = "spam_flags"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, unique=True)
    type = Column(spamless_filter_types, nullable=False)
    points = Column(Integer, default=0)
    muted = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message.to_dict(),
            "type": self.type,
            "points": self.points,
            "muted": self.muted,
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
    postgresql_where=GroupChat.publicity.in_(("listed", "pinned")),
)

# Index for your chats list.
Index("chat_users_user_id_subscribed", ChatUser.user_id, ChatUser.subscribed)

# Index for user number lookup.
Index("chat_users_number_unique", ChatUser.chat_id, ChatUser.number, unique=True)

# Index to make log rendering easier.
Index("messages_chat_id", Message.chat_id, Message.posted)

# Index for searching characters by tag.
Index("character_tags_tag_id", CharacterTag.tag_id)

# Index to make tag type/name combo unique.
Index("tags_type_name", Tag.type, Tag.name, unique=True)


# 3. Relationships

User.admin_tier = relation(AdminTier, backref="users")
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

UserNote.user = relation(User, primaryjoin=UserNote.user_id == User.id)
UserNote.creator = relation(User, primaryjoin=UserNote.creator_id == User.id)

Block.blocking_user = relation(User, primaryjoin=Block.blocking_user_id == User.id)
Block.blocked_user = relation(User, primaryjoin=Block.blocked_user_id == User.id)
Block.chat = relation(Chat)
Block.blocked_chat_user = relation(
    ChatUser,
    primaryjoin=and_(
        Block.chat_id == ChatUser.chat_id,
        Block.blocked_user_id == ChatUser.user_id,
    ),
    foreign_keys=[Block.chat_id, Block.blocked_user_id],
)

Character.search_character = relation(SearchCharacter, backref="characters")
Character.tags = relation(CharacterTag, backref="character", order_by=CharacterTag.alias)

Fandom.groups = relation(SearchCharacterGroup, backref="fandom", order_by=SearchCharacterGroup.order)
SearchCharacterGroup.characters = relation(SearchCharacter, backref="group", order_by=SearchCharacter.order)

SearchCharacterChoice.user = relation(User, backref="search_character_choices")
SearchCharacterChoice.character = relation(SearchCharacter, backref="users")

GroupChat.creator = relation(User, backref="created_chats")
GroupChat.parent = relation(
    Chat,
    backref="children",
    primaryjoin=GroupChat.parent_id == Chat.id,
)

LogMarker.chat = relation(Chat, backref="log_markers")
LogMarker.message = relation(Message, backref="log_marker")

ChatUser.user = relation(User, backref="chats")
ChatUser.chat = relation(Chat, backref="users")
ChatUser.search_character = relation(SearchCharacter, backref="chat_users")

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

Tag.characters = relation(CharacterTag, backref="tag")
Tag.synonym_of = relation(Tag, backref="synonyms", remote_side=Tag.id)

AdminLogEntry.action_user = relation(User, backref="admin_actions", foreign_keys=AdminLogEntry.action_user_id)
AdminLogEntry.affected_user = relation(User, foreign_keys=AdminLogEntry.affected_user_id)
AdminLogEntry.chat = relation(Chat)

IPBan.creator = relation(User)
EmailBan.creator = relation(User)

AdminTier.admin_tier_permissions = relation(AdminTierPermission, backref="admin_tier")
AdminTier.permissions = association_proxy(
    "admin_tier_permissions", "permission",
    creator=lambda permission: AdminTierPermission(permission=permission),
)

SpamFlag.message = relation(Message) # no backref for now so it doesn't collide with the spam_flag field

