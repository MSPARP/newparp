from celery import chord
from celery.utils.log import get_task_logger
from random import shuffle
from sqlalchemy import and_, func, or_
from uuid import uuid4

from newparp.helpers.matchmaker import fetch_searcher, option_messages
from newparp.model import Block, ChatUser, Message, SearchedChat, User
from newparp.tasks import celery, WorkerTask

logger = get_task_logger(__name__)


@celery.task(base=WorkerTask, queue="worker")
def generate_searching_counter():
    redis = generate_searching_counter.redis

    pipe = redis.pipeline()
    for searcher_id in redis.smembers("searchers"):
        pipe.get("searcher:%s:session_id" % searcher_id)

    for session_id in set(pipe.execute()):
        if session_id:
            pipe.get("session:%s" % session_id)

    redis.set("searching_users", len(set(pipe.execute())))


@celery.task(base=WorkerTask, queue="matchmaker")
def new_searcher(searcher_id):
    redis = new_searcher.redis

    logger.debug("new searcher: %s")
    searchers = redis.smembers("searchers")

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

    s1 = fetch_searcher(redis, searcher_id_1)
    s2 = fetch_searcher(redis, searcher_id_2)

    alive = True
    for searcher in (s1, s2):
        if not all(searcher[:-2]):
            logger.debug("%s not alive" % searcher.id)
            redis.srem("searchers", searcher.id)
            alive = False
    if not alive:
        return None, None

    # Don't pair people with themselves.
    if s1.user_id == s2.user_id:
        return None, None

    # Don't match if they've already been paired up recently.
    match_key = "matched:%s:%s" % tuple(sorted([s1.user_id, s2.user_id]))
    if redis.exists(match_key):
        return None, None

    options = []

    # Style options should be matched with themselves or "either".
    if s1.style != "either" and s2.style != "either" and s1.style != s2.style:
        return None, None
    if s1.style != "either":
        options.append(s1.style)
    elif s2.style != "either":
        options.append(s2.style)

    # Levels have to overlap.
    levels_in_common = s1.levels & s2.levels
    logger.debug("Levels in common: %s" % levels_in_common)
    if levels_in_common:
        options.append(
            "nsfw-extreme" if "nsfw-extreme" in levels_in_common
            else "nsfw" if "nsfw" in levels_in_common
            else "sfw"
        )
    else:
        return None, None

    # Check filters.
    s1_name = s1.character["name"].lower().encode("utf8")
    for search_filter in s2.filters:
        search_filter = search_filter.encode("utf8")
        logger.debug("comparing %s and %s" % (s1_name, search_filter))
        if search_filter in s1_name:
            logger.debug("FILTER %s MATCHED" % search_filter)
            return None, None
    s2_name = s2.character["name"].lower().encode("utf8")
    for search_filter in s1.filters:
        search_filter = search_filter.encode("utf8")
        logger.debug("comparing %s and %s" % (s2_name, search_filter))
        if search_filter in s2_name:
            logger.debug("FILTER %s MATCHED" % search_filter)
            return None, None

    if (
        # Match if either person has wildcard, or if they're otherwise compatible.
        (len(s2.choices) == 0 or s1.search_character_id in s2.choices)
        and (len(s1.choices) == 0 or s2.search_character_id in s1.choices)
    ):
        # don't do this until comparison_callback
        return s2.id, options

    return None, None


@celery.task(base=WorkerTask, queue="matchmaker")
def comparison_callback(results, searcher_id_1):
    redis = comparison_callback.redis
    db = comparison_callback.db

    if redis.exists("lock:matchmaker"):
        logger.debug("locked. calling again in 1 second.")
        comparison_callback.apply_async((results, searcher_id_1), countdown=1)
        return
    redis.setex("lock:matchmaker", 60, 1)

    # Check if there's a match.
    matched_searchers = [_ for _ in results if _[0] is not None]
    if not matched_searchers:
        logger.debug("no results")
        redis.delete("lock:matchmaker")
        return
    logger.debug("results: %s" % matched_searchers)
    shuffle(matched_searchers)

    # Fetch searcher 1.
    s1 = fetch_searcher(redis, searcher_id_1)
    if not all(s1[:-2]):
        logger.debug("%s has expired" % searcher_id_1)
        redis.delete("lock:matchmaker")
        return

    # Pick a second searcher from the matches.
    for searcher_id_2, options in matched_searchers:
        s2 = fetch_searcher(redis, searcher_id_2)
        if all(s2[:-2]) and db.query(func.count("*")).select_from(Block).filter(or_(
            and_(Block.blocking_user_id == s1.user_id, Block.blocked_user_id == s2.user_id),
            and_(Block.blocking_user_id == s2.user_id, Block.blocked_user_id == s1.user_id),
        )).scalar() == 0:
            logger.debug("matched %s" % searcher_id_2)
            break
    else:
        logger.debug("all matches have expired")
        redis.delete("lock:matchmaker")
        return

    new_url = str(uuid4()).replace("-", "")
    logger.info("matched %s and %s, sending to %s." % (s1.id, s2.id, new_url))
    new_chat = SearchedChat(url=new_url)
    db.add(new_chat)
    db.flush()

    s1_user = db.query(User).filter(User.id == s1.user_id).one()
    s2_user = db.query(User).filter(User.id == s2.user_id).one()
    db.add(ChatUser.from_user(s1_user, chat_id=new_chat.id, number=1, search_character_id=s1.search_character_id, **s1.character))
    if s1_user != s2_user:
        db.add(ChatUser.from_user(s2_user, chat_id=new_chat.id, number=2, search_character_id=s2.search_character_id, **s2.character))

    if options:
        db.add(Message(
            chat_id=new_chat.id,
            type="search_info",
            text=" ".join(option_messages[_] for _ in options),
        ))

    db.commit()

    pipe = redis.pipeline()
    match_key = "matched:%s:%s" % tuple(sorted([s1.user_id, s2.user_id]))
    pipe.set(match_key, 1)
    pipe.expire(match_key, 1800)
    pipe.srem("searchers", s1.id, s2.id)
    match_message = """{"status":"matched","url":"%s"}""" % new_url
    pipe.publish("searcher:%s" % s1.id, match_message)
    pipe.publish("searcher:%s" % s2.id, match_message)
    pipe.delete("lock:matchmaker")
    pipe.execute()

