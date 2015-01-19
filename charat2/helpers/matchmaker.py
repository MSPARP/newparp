import time
import json
import logging

from random import shuffle
from redis import StrictRedis
from uuid import uuid4

from charat2.model import sm, ChatUser, Message
from charat2.model.connections import redis_pool

option_messages = {
    "script": "This is a script style chat.",
    "paragraph": "This is a paragraph style chat.",
    "sfw": "Please keep this chat safe for work.",
    "nsfw": "NSFW content is allowed.",
}


def run_matchmaker(
    searchers_key, searcher_prefix, get_searcher_info, check_compatibility,
    ChatClass, get_character_info,
):

    # XXX get log level from stdin
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    db = sm()
    redis = StrictRedis(connection_pool=redis_pool)

    searcher_ids = redis.smembers(searchers_key)

    while True:

        # Reset the searcher list for the next iteration.
        redis.delete(searchers_key)
        for searcher in searcher_ids:
            logging.debug("Waking unmatched searcher %s." % searcher)
            redis.publish("%s:%s" % (searcher_prefix, searcher), "{ \"status\": \"unmatched\" }")

        time.sleep(10)

        logging.info("Starting match loop.")

        searcher_ids = redis.smembers(searchers_key)

        # We can't do anything with less than 2 people, so don't bother.
        if len(searcher_ids) < 2:
            logging.info("Not enough searchers, skipping.")
            continue

        searchers = get_searcher_info(redis, searcher_ids)
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

                match, options = check_compatibility(redis, s1, s2)
                if not match:
                    logging.debug("No match.")
                    continue

                new_url = str(uuid4()).replace("-", "")
                logging.info(
                    "Matched %s and %s, sending to %s."
                    % (s1["id"], s2["id"], new_url)
                )
                new_chat = ChatClass(url=new_url)
                db.add(new_chat)
                db.flush()

                db.add(ChatUser(chat_id=new_chat.id, user_id=s1["user_id"], number=1, **get_character_info(db, s1)))
                db.add(ChatUser(chat_id=new_chat.id, user_id=s2["user_id"], number=2, **get_character_info(db, s2)))

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

