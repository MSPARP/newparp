#!/usr/bin/python

from charat2.helpers.matchmaker import run_matchmaker
from charat2.model import RouletteChat, SearchCharacter


def get_searcher_info(redis, searcher_ids):
    searchers = []
    for searcher_id in searcher_ids:
        session_id = redis.get("roulette:%s:session_id" % searcher_id)
        # This will fail they've logged out since sending the request.
        try:
            searchers.append({
                "id": searcher_id,
                "user_id": int(redis.get("session:%s" % session_id)),
                "search_character_id": int(redis.get("roulette:%s:search_character_id" % searcher_id))
            })
        except (TypeError, ValueError):
            continue
    return searchers


def check_compatibility(redis, s1, s2):
	# Don't pair people with themselves.
    if s1["user_id"] == s2["user_id"]:
        return False, ("roulette",)
    # Don't match if they've already been paired up recently.
    match_key = "matched:%s:%s" % tuple(sorted([s1["user_id"], s2["user_id"]]))
    if redis.exists(match_key):
        return False, ("roulette",)
    redis.set(match_key, 1)
    redis.expire(match_key, 1800)
    return True, ("roulette",)


def get_character_info(db, searcher):
    try:
        character = db.query(SearchCharacter).filter(
            SearchCharacter.id == searcher["search_character_id"],
        ).one()
    except NoResultFound:
        return {}
    return {
        "name": character.name,
        "alias": character.alias,
        "color": character.color,
        "quirk_prefix": character.quirk_prefix,
        "quirk_suffix": character.quirk_suffix,
        "case": character.case,
        "replacements": character.replacements,
        "regexes": character.regexes,
    }


if __name__ == "__main__":
    run_matchmaker(
        "roulette_searchers", "roulette", get_searcher_info, check_compatibility,
        RouletteChat, get_character_info,
    )

