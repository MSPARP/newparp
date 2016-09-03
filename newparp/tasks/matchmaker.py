from celery import chord
from celery.utils.log import get_task_logger

from newparp.helpers.matchmaker import run_matchmaker, fetch_searcher
from newparp.model import SearchedChat
from newparp.tasks import celery, WorkerTask

logger = get_task_logger(__name__)

def get_searcher_info(redis, searcher_ids):
    searchers = []
    for searcher_id in searcher_ids:
        session_id = redis.get("searcher:%s:session_id" % searcher_id)
        # This will fail if they've logged out since sending the request.
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
            "style": redis.get("searcher:%s:style" % searcher_id),
            "levels": redis.smembers("searcher:%s:levels" % searcher_id),
            "filters": redis.lrange("searcher:%s:filters" % searcher_id, 0, -1),
            "choices": {int(_) for _ in redis.smembers("searcher:%s:choices" % searcher_id)},
        })
    return searchers


def check_compatibility(redis, s1, s2):

    # Don't pair people with themselves.
    if s1["user_id"] == s2["user_id"]:
        return False, None

    # Don't match if they've already been paired up recently.
    match_key = "matched:%s:%s" % tuple(sorted([s1["user_id"], s2["user_id"]]))
    if redis.exists(match_key):
        return False, None

    options = []

    # Style options should be matched with themselves or "either".
    if (
        s1["style"] != "either"
        and s2["style"] != "either"
        and s1["style"] != s2["style"]
    ):
        return False, None
    if s1["style"] != "either":
        options.append(s1["style"])
    elif s2["style"] != "either":
        options.append(s2["style"])

    # Levels have to overlap.
    levels_in_common = s1["levels"] & s2["levels"]
    logger.debug("Levels in common: %s" % levels_in_common)
    if levels_in_common:
        options.append(
            "nsfw-extreme" if "nsfw-extreme" in levels_in_common
            else "nsfw" if "nsfw" in levels_in_common
            else "sfw"
        )
    else:
        return False, None

    # Check filters.
    s1_name = s1["character"]["name"].lower().encode("utf8")
    for search_filter in s2["filters"]:
        search_filter = search_filter.encode("utf8")
        logger.debug("comparing %s and %s" % (s1_name, search_filter))
        if search_filter in s1_name:
            logger.debug("FILTER %s MATCHED" % search_filter)
            return False, None
    s2_name = s2["character"]["name"].lower().encode("utf8")
    for search_filter in s1["filters"]:
        search_filter = search_filter.encode("utf8")
        logger.debug("comparing %s and %s" % (s2_name, search_filter))
        if search_filter in s2_name:
            logger.debug("FILTER %s MATCHED" % search_filter)
            return False, None

    if (
        # Match if either person has wildcard, or if they're otherwise compatible.
        (len(s2["choices"]) == 0 or s1["search_character_id"] in s2["choices"])
        and (len(s1["choices"]) == 0 or s2["search_character_id"] in s1["choices"])
    ):
        redis.set(match_key, 1)
        redis.expire(match_key, 1800)
        return True, options

    return False, None


def get_character_info(db, searcher):
    return searcher["character"]


@celery.task(base=WorkerTask, queue="worker")
def run():
    db = run.db
    redis = run.redis

    run_matchmaker(
        db, redis, 2, "searchers", "searcher", get_searcher_info,
        check_compatibility, SearchedChat, get_character_info,
    )


@celery.task(base=WorkerTask, queue="matchmaker")
def new_searcher(searcher_id):
    # TODO lock
    logger.debug("new searcher: %s")
    searchers = new_searcher.redis.smembers("searchers")
    try:
        searchers.remove(searcher_id)
    except KeyError:
        logger.debug("no longer searching")
        return
    if not searchers:
        logger.debug("not enough searchers, skipping")
        return
    chord(
        (compare.s(searcher_id, _) for _ in searchers if _ != searcher_id),
        comparison_callback.s(searcher_id),
    ).delay()


@celery.task(base=WorkerTask, queue="matchmaker")
def compare(searcher_id_1, searcher_id_2):
    redis = compare.redis
    logger.debug("comparing %s and %s" % (searcher_id_1, searcher_id_2))

    s1 = fetch_searcher(compare.redis, searcher_id_1)
    logger.debug(s1)
    s2 = fetch_searcher(compare.redis, searcher_id_2)
    logger.debug(s2)

    alive = True
    for searcher in (s1, s2):
        if not all(searcher[:-2]):
            logger.debug("%s not alive" % searcher.id)
            redis.srem("searchers", searcher.id)
            alive = False
    if not alive:
        return False

    options = {}

    if (
        # Match if either person has wildcard, or if they're otherwise compatible.
        (len(s2.choices) == 0 or s1.search_character_id in s2.choices)
        and (len(s1.choices) == 0 or s2.search_character_id in s1.choices)
    ):
        # don't do this until comparison_callback
        #redis.set(match_key, 1)
        #redis.expire(match_key, 1800)
        return True, options

    return False, None


@celery.task(base=WorkerTask, queue="matchmaker")
def comparison_callback(results, searcher_id):
    logger.debug("match results: %s" % results)
    matched_searchers = [_ for _ in results if _[0] is True]
    if not matched_searchers:
        logger.debug("no results")
        return
    logger.debug("results: %s" % matched_searchers)






