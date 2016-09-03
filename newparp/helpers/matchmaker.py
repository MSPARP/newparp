import os
import json
import logging

from random import shuffle
from sqlalchemy import and_, func
from uuid import uuid4

from newparp.model import Block, ChatUser, Message, User


def validate_searcher_exists(redis, searcher_id):
    """Check whether a searcher's mandatory keys are present."""
    return redis.eval("""local session_id = redis.call("get", "searcher:"..ARGV[1]..":session_id") or "-"
    return {
        session_id,
        redis.call("get",   "session:"..session_id),
        redis.call("get",   "searcher:"..ARGV[1]..":search_character_id"),
        redis.call("hlen",  "searcher:"..ARGV[1]..":character"),
        redis.call("get",   "searcher:"..ARGV[1]..":style"),
        redis.call("scard", "searcher:"..ARGV[1]..":levels"),
    }""", 0, searcher_id)


def validate_searcher_is_searching(redis, searcher_id):
    """Check whether a searcher's mandatory keys are present and they're in the searchers set."""
    return redis.eval("""local session_id = redis.call("get", "searcher:"..ARGV[1]..":session_id") or "-"
    return {
        redis.call("sismember", "searchers", ARGV[1]),
        session_id,
        redis.call("get",   "session:"..session_id),
        redis.call("get",   "searcher:"..ARGV[1]..":search_character_id"),
        redis.call("hlen",  "searcher:"..ARGV[1]..":character"),
        redis.call("get",   "searcher:"..ARGV[1]..":style"),
        redis.call("scard", "searcher:"..ARGV[1]..":levels"),
    }""", 0, searcher_id)


def refresh_searcher(redis, searcher_id):
    """Reset the expiry times on a searcher's keys."""
    return redis.eval("""local session_id = redis.call("get", "searcher:"..ARGV[1]..":session_id") or "-"
    return {
        redis.call("get",       "session:"..session_id),
        redis.call("sismember", "searchers", ARGV[1]),
        redis.call("expire",    "searcher:"..ARGV[1]..":session_id",          30),
        redis.call("expire",    "searcher:"..ARGV[1]..":search_character_id", 30),
        redis.call("expire",    "searcher:"..ARGV[1]..":character",           30),
        redis.call("expire",    "searcher:"..ARGV[1]..":style",               30),
        redis.call("expire",    "searcher:"..ARGV[1]..":levels",              30),
        redis.call("expire",    "searcher:"..ARGV[1]..":filters",             30),
        redis.call("expire",    "searcher:"..ARGV[1]..":choices",             30),
    }""", 0, searcher_id)


def fetch_searcher(redis, searcher_id):
    """Fetch searcher keys for matching."""
    return redis.eval("""local session_id = redis.call("get", "searcher:"..ARGV[1]..":session_id") or "-"
    return {
        redis.call("sismember", "searchers", ARGV[1]),
        session_id,
        redis.call("get",      "session:"..session_id),
        redis.call("get",      "searcher:"..ARGV[1]..":search_character_id"),
        redis.call("hget",     "searcher:"..ARGV[1]..":character", "name"),
        redis.call("get",      "searcher:"..ARGV[1]..":style"),
        redis.call("smembers", "searcher:"..ARGV[1]..":levels"),
        redis.call("lrange",    "searcher:"..ARGV[1]..":filters",             30),
        redis.call("expire",    "searcher:"..ARGV[1]..":choices",             30),
    }""", 0, searcher_id)


option_messages = {
    "script": "This is a script style chat.",
    "paragraph": "This is a paragraph style chat.",
    "sfw": "Please keep this chat safe for work.",
    "nsfw": "NSFW content is allowed.",
    "nsfw-extreme": "Extreme NSFW content is allowed.",
    "roulette": "TT: There is a 98.413% chance that you have just connected to someone anonymously. It seems that you should probably say \"Hello\" now.",
}


def wake_unmatched_searchers(redis, searcher_prefix, searcher_ids):
    for searcher in searcher_ids:
        logging.debug("Waking unmatched searcher %s." % searcher)
        redis.publish("%s:%s" % (searcher_prefix, searcher), "{ \"status\": \"unmatched\" }")


def run_matchmaker(
    db, redis, lock_id, searchers_key, searcher_prefix, get_searcher_info,
    check_compatibility, ChatClass, get_character_info
):

    root = logging.getLogger()
    if 'DEBUG' in os.environ:
        root.setLevel(logging.DEBUG)

    searcher_ids = redis.smembers(searchers_key)

    # Reset the searcher list for the next iteration.
    redis.delete(searchers_key)

    logging.debug("Starting match loop.")

    # We can't do anything with less than 2 people, so don't bother.
    if len(searcher_ids) < 2:
        logging.debug("Not enough searchers, skipping.")
        wake_unmatched_searchers(redis, searcher_prefix, searcher_ids)
        redis.set(
            "searching_users" if searchers_key == "searchers" else "rouletting_users",
            len(searcher_ids),
        )
        return

    searchers = get_searcher_info(redis, searcher_ids)
    logging.debug("Searcher list: %s" % searchers)

    redis.set(
        "searching_users" if searchers_key == "searchers" else "rouletting_users",
        len({_["user_id"] for _ in searchers}),
    )

    shuffle(searchers)

    already_matched = set()
    # Range hack so we don't check opposite pairs or against itself.
    for n in range(len(searchers)):
        s1 = searchers[n]

        for m in range(n + 1, len(searchers)):
            s2 = searchers[m]

            if s1["id"] in already_matched or s2["id"] in already_matched:
                continue

            logging.debug("Comparing %s and %s." % (s1["id"], s2["id"]))

            match, options = check_compatibility(redis, s1, s2)
            if not match:
                logging.debug("No match.")
                continue

            blocked = (
                db.query(func.count("*")).select_from(Block).filter(and_(
                    Block.blocking_user_id == s1["user_id"],
                    Block.blocked_user_id == s2["user_id"]
                )).scalar() != 0
                or db.query(func.count("*")).select_from(Block).filter(and_(
                    Block.blocking_user_id == s2["user_id"],
                    Block.blocked_user_id == s1["user_id"]
                )).scalar() != 0
            )
            if blocked:
                logging.debug("Blocked.")
                continue

            new_url = str(uuid4()).replace("-", "")
            logging.info(
                "Matched %s and %s, sending to %s."
                % (s1["id"], s2["id"], new_url)
            )
            new_chat = ChatClass(url=new_url)
            db.add(new_chat)
            db.flush()

            s1_user = db.query(User).filter(User.id == s1["user_id"]).one()
            s2_user = db.query(User).filter(User.id == s2["user_id"]).one()
            db.add(ChatUser.from_user(s1_user, chat_id=new_chat.id, number=1, search_character_id=s1["search_character_id"], **get_character_info(db, s1)))
            db.add(ChatUser.from_user(s2_user, chat_id=new_chat.id, number=2, search_character_id=s2["search_character_id"], **get_character_info(db, s2)))

            if options:
                db.add(Message(
                    chat_id=new_chat.id,
                    type="search_info",
                    text=" ".join(option_messages[_] for _ in options),
                ))

            db.commit()

            already_matched.add(s1["id"])
            already_matched.add(s2["id"])

            match_message = json.dumps({ "status": "matched", "url": new_url })
            redis.publish("%s:%s" % (searcher_prefix, s1["id"]), match_message)
            redis.publish("%s:%s" % (searcher_prefix, s2["id"]), match_message)
            searcher_ids.remove(s1["id"])
            searcher_ids.remove(s2["id"])

    wake_unmatched_searchers(redis, searcher_prefix, searcher_ids)

