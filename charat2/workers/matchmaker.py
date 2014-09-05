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
from charat2.model import sm, ChatUser, Message, SearchedChat, UserCharacter
from charat2.model.connections import redis_pool


def check_compatibility(s1, s2):

    # Normal tags.
    if len(s1["tags"]) == 0 and len(s2["tags"]) == 0:
        logging.debug("Neither session has tags.")
        tags_in_common = set()
    else:
        tags_in_common = s1["tags"] & s2["tags"]
        logging.debug("Tags in common: %s" % tags_in_common)
        if len(tags_in_common) == 0:
            return None

    s1_exclusions = s1["exclude_tags"] & s2["tags"]
    s2_exclusions = s2["exclude_tags"] & s1["tags"]
    if len(s1_exclusions) > 0 or len(s2_exclusions) > 0:
        logging.debug("Session %s excludes %s" % (s1["id"], s1_exclusions))
        logging.debug("Session %s excludes %s" % (s2["id"], s2_exclusions))
        return None

    return { "tags_in_common": tags_in_common }


def set_user_character(chat_id, searcher):
    if searcher["character_id"] is None:
        logging.debug("No character ID specified for %s." % searcher["id"])
        return
    try:
        character_id = int(searcher["character_id"])
        user_id = int(redis.get("session:%s" % searcher["id"]))
        logging.debug(
            "Setting character for %s: user %s, character %s."
            % (searcher["id"], user_id, character_id)
        )
        character = db.query(UserCharacter).filter(and_(
            UserCharacter.id == character_id,
            UserCharacter.user_id == user_id,
        )).options(joinedload(UserCharacter.user)).one()
    except ValueError:
        logging.debug("No character, character ID or user ID not valid.")
        return
    except NoResultFound:
        logging.debug("No character, character not found.")
        return
    logging.debug(
        "Found character %s [%s]." % (character.name, character.alias)
    )
    db.add(ChatUser.from_character(character, chat_id=chat_id))


if __name__ == "__main__":

    # XXX get log level from stdin
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    db = sm()
    redis = StrictRedis(connection_pool=redis_pool)

    searchers = redis.smembers("searchers")

    while True:

        # Reset the searcher list for the next iteration.
        redis.delete("searchers")
        for searcher in searchers:
            logging.debug("Waking unmatched searcher %s." % searcher)
            redis.publish("searcher:%s" % searcher, "{ \"status\": \"unmatched\" }")

        time.sleep(10)

        logging.info("Starting match loop.")

        searchers = redis.smembers("searchers")

        # We can't do anything with less than 2 people, so don't bother.
        if len(searchers) < 2:
            logging.info("Not enough searchers, skipping.")
            continue

        sessions = [{
            "id": _,
            "character_id": redis.get("session:%s:character_id" % _),
            "tags": redis.smembers("session:%s:tags" % _),
            "exclude_tags": redis.smembers("session:%s:exclude_tags" % _),
        } for _ in searchers]
        logging.debug("Session list: %s" % sessions)
        shuffle(sessions)

        already_matched = set()
        # Range hack so we don't check opposite pairs or against itself.
        for n in range(len(sessions)):
            s1 = sessions[n]

            for m in range(n + 1, len(sessions)):
                s2 = sessions[m]

                if s1["id"] in already_matched or s2["id"] in already_matched:
                    continue

                logging.debug("Comparing %s and %s." % (s1["id"], s2["id"]))

                match = check_compatibility(s1, s2)
                if match is None:
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

                if len(match["tags_in_common"]) > 0:
                    send_message(db, redis, Message(
                        chat_id=new_chat.id,
                        type="search_info",
                        text=(
                            "Tags in common: %s."
                            % (", ".join(sorted(match["tags_in_common"])))
                        ),
                    ))

                set_user_character(new_chat.id, s1)
                set_user_character(new_chat.id, s2)

                db.commit()

                already_matched.add(s1["id"])
                already_matched.add(s2["id"])

                match_message = json.dumps({ "status": "matched", "url": new_url })
                redis.publish("searcher:%s" % s1["id"], match_message)
                redis.publish("searcher:%s" % s2["id"], match_message)
                searchers.remove(s1["id"])
                searchers.remove(s2["id"])

