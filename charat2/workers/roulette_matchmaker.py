#!/usr/bin/python

import time
import json
import logging

from random import shuffle
from redis import StrictRedis

from uuid import uuid4

from charat2.model import sm, ChatUser, RouletteChat
from charat2.model.connections import redis_pool


if __name__ == "__main__":

    # XXX get log level from stdin
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    db = sm()
    redis = StrictRedis(connection_pool=redis_pool)

    searcher_ids = redis.smembers("roulette_searchers")

    while True:

        # Reset the searcher list for the next iteration.
        redis.delete("roulette_searchers")
        for searcher in searcher_ids:
            logging.debug("Waking unmatched searcher %s." % searcher)
            redis.publish("roulette:%s" % searcher, "{ \"status\": \"unmatched\" }")

        time.sleep(10)

        logging.info("Starting match loop.")

        searcher_ids = redis.smembers("roulette_searchers")

        # We can't do anything with less than 2 people, so don't bother.
        if len(searcher_ids) < 2:
            logging.info("Not enough searchers, skipping.")
            continue

        searchers = []
        for searcher in searcher_ids:
            session_id = redis.get("roulette:%s:session_id" % searcher)
            # Don't match them if they've logged out since sending the request.
            #try:
            if True:
                searchers.append({
                    "id": searcher,
                    "user_id": int(redis.get("session:%s" % session_id)),
                })
            #except (TypeError, ValueError):
            #    continue

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

                if s1["user_id"] == s2["user_id"]:
                    logging.info(
                        "Not matching %s and %s - same user."
                        % (s1["id"], s2["id"])
                    )
                    continue

                new_url = str(uuid4()).replace("-", "")
                logging.info(
                    "Matched %s and %s, sending to %s."
                    % (s1["id"], s2["id"], new_url)
                )
                new_chat = RouletteChat(url=new_url)
                db.add(new_chat)
                db.flush()

                db.add(ChatUser(chat_id=new_chat.id, user_id=s1["user_id"], number=1))
                db.add(ChatUser(chat_id=new_chat.id, user_id=s2["user_id"], number=2))

                db.commit()

                already_matched.add(s1["id"])
                already_matched.add(s2["id"])

                match_message = json.dumps({ "status": "matched", "url": new_url })
                redis.publish("roulette:%s" % s1["id"], match_message)
                redis.publish("roulette:%s" % s2["id"], match_message)
                searcher_ids.remove(s1["id"])
                searcher_ids.remove(s2["id"])

