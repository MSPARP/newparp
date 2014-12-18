#!/usr/bin/python

import time
import json
import logging

from random import shuffle
from redis import StrictRedis
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4

from charat2.helpers.chat import send_message
from charat2.model import sm, ChatUser, Message, SearchedChat, User
from charat2.model.connections import redis_pool


option_messages = {
    "script": "This is a script style chat.",
    "paragraph": "This is a paragraph style chat.",
    "sfw": "Please keep this chat safe for work.",
    "nsfw": "NSFW content is allowed.",
}


def check_compatibility(s1, s2):

    # Don't pair people with themselves.
    if s1["user_id"] == s2["user_id"]:
        return False, None

    options = []

    # Style options should be matched with themselves or "either".
    if (
        s1["options"]["style"] != "either"
        and s2["options"]["style"] != "either"
        and s1["options"]["style"] != s2["options"]["style"]
    ):
        return False, None
    if s1["options"]["style"] != "either":
        options.append(s1["options"]["style"])
    elif s2["options"]["style"] != "either":
        options.append(s2["options"]["style"])

    # Level has to be the same.
    if s1["options"]["level"] != s2["options"]["level"]:
        return False, None
    else:
        options.append(s1["options"]["level"])

    # Match people who both chose wildcard.
    if not s1["choices"] and not s2["choices"]:
        return True, options

    # Match people who are otherwise compatible.
    if s1["search_character_id"] in s2["choices"] and s2["search_character_id"] in s1["choices"]:
        return True, options

    return False, None


if __name__ == "__main__":

    # XXX get log level from stdin
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    db = sm()
    redis = StrictRedis(connection_pool=redis_pool)

    searcher_ids = redis.smembers("searchers")

    while True:

        # Reset the searcher list for the next iteration.
        redis.delete("searchers")
        for searcher in searcher_ids:
            logging.debug("Waking unmatched searcher %s." % searcher)
            redis.publish("searcher:%s" % searcher, "{ \"status\": \"unmatched\" }")

        time.sleep(10)

        logging.info("Starting match loop.")

        searcher_ids = redis.smembers("searchers")

        # We can't do anything with less than 2 people, so don't bother.
        if len(searcher_ids) < 2:
            logging.info("Not enough searchers, skipping.")
            continue

        searchers = []
        for searcher in searcher_ids:
            session_id = redis.get("searcher:%s:session_id" % searcher)
            # Don't match them if they've logged out since sending the request.
            try:
                user_id = int(redis.get("session:%s" % session_id))
                search_character_id = int(redis.get("searcher:%s:search_character_id" % searcher))
            except ValueError:
                continue
            searchers.append({
                "id": searcher,
                "user_id": user_id,
                "search_character_id": search_character_id,
                "character": redis.hgetall("searcher:%s:character" % searcher),
                "options": redis.hgetall("searcher:%s:options" % searcher),
                "choices": {int(_) for _ in redis.smembers("searcher:%s:choices" % searcher)},
            })
        logging.debug("Searcher list: %s" % searchers)
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

                match, options = check_compatibility(s1, s2)
                if not match:
                    logging.debug("No match.")
                    continue

                new_url = str(uuid4()).replace("-", "")
                logging.info(
                    "Matched %s and %s, sending to %s."
                    % (s1["id"], s2["id"], new_url)
                )
                new_chat = SearchedChat(url=new_url)
                db.add(new_chat)
                db.flush()

                db.add(ChatUser(chat_id=new_chat.id, user_id=s1["user_id"], **s1["character"]))
                db.add(ChatUser(chat_id=new_chat.id, user_id=s2["user_id"], **s2["character"]))

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
                redis.publish("searcher:%s" % s1["id"], match_message)
                redis.publish("searcher:%s" % s2["id"], match_message)
                searcher_ids.remove(s1["id"])
                searcher_ids.remove(s2["id"])

