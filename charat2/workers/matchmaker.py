#!/usr/bin/python

from charat2.helpers.matchmaker import run_matchmaker
from charat2.model import SearchedChat


def get_searcher_info(redis, searcher_ids):
    searchers = []
    for searcher_id in searcher_ids:
        session_id = redis.get("searcher:%s:session_id" % searcher_id)
        # This will fail they've logged out since sending the request.
        try:
            user_id = int(redis.get("session:%s" % session_id))
            search_character_id = int(redis.get("searcher:%s:search_character_id" % searcher_id))
        except (TypeError, ValueError):
            continue
        searchers.append({
            "id": searcher_id,
            "user_id": user_id,
            "search_character_id": search_character_id,
            "character": redis.hgetall("searcher:%s:character" % searcher_id),
            "options": redis.hgetall("searcher:%s:options" % searcher_id),
            "choices": {int(_) for _ in redis.smembers("searcher:%s:choices" % searcher_id)},
        })
    return searchers


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


def get_character_info(db, searcher):
    return searcher["character"]


if __name__ == "__main__":
    run_matchmaker(get_searcher_info, check_compatibility, SearchedChat, get_character_info)

