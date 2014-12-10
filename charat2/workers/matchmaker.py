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


def check_compatibility(s1, s2):
    # Don't pair people with themselves.
    if s1["user"].id == s2["user"].id:
        return False
    # Match people who both chose wildcard.
    if not s1["choices"] and not s2["choices"]:
        return True
    # Match people who are otherwise compatible.
    if s1["user"].search_character_id in s2["choices"] and s2["user"].search_character_id in s1["choices"]:
        return True
    return False


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

        # Make sure we have a new transaction for each loop.
        db.commit()

        searchers = []
        for searcher in searcher_ids:
            session_id = redis.get("searcher:%s:session_id" % searcher)
            # Don't match them if they've logged out since sending the request.
            try:
                user = db.query(User).filter(
                    User.id == int(redis.get("session:%s" % session_id)),
                ).options(joinedload(User.search_character_choices)).one()
            except ValueError, NoResultFound:
                continue
            searchers.append({
                "id": searcher, "user": user,
                "choices": {_.search_character_id for _ in user.search_character_choices},
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

                match = check_compatibility(s1, s2)
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

                db.commit()

                already_matched.add(s1["id"])
                already_matched.add(s2["id"])

                match_message = json.dumps({ "status": "matched", "url": new_url })
                redis.publish("searcher:%s" % s1["id"], match_message)
                redis.publish("searcher:%s" % s2["id"], match_message)
                searcher_ids.remove(s1["id"])
                searcher_ids.remove(s2["id"])

