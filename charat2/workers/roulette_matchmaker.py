#!/usr/bin/python

from charat2.helpers.matchmaker import run_matchmaker
from charat2.model import RouletteChat


def get_searcher_info(redis, searcher_ids):
    searchers = []
    for searcher_id in searcher_ids:
        session_id = redis.get("roulette:%s:session_id" % searcher_id)
        # This will fail they've logged out since sending the request.
        try:
            searchers.append({
                "id": searcher_id,
                "user_id": int(redis.get("session:%s" % session_id)),
            })
        except (TypeError, ValueError):
            continue
    return searchers


def check_compatibility(redis, s1, s2):
	# Don't pair people with themselves.
    if s1["user_id"] == s2["user_id"]:
        return False, None
    # Don't match if they've already been paired up recently.
    match_key = "matched:%s:%s" % tuple(sorted([s1["user_id"], s2["user_id"]]))
    if redis.exists(match_key):
        return False, None
    redis.set(match_key, 1)
    redis.expire(match_key, 1800)
    return True, None


def get_character_info(db, searcher):
    return {}


if __name__ == "__main__":
    run_matchmaker(
        "roulette_searchers", "roulette", get_searcher_info, check_compatibility,
        RouletteChat, get_character_info,
    )
