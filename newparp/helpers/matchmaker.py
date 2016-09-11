from collections import namedtuple

def validate_searcher_exists(redis, searcher_id):
    """Check whether a searcher's mandatory keys are present."""
    return redis.eval("""local session_id = redis.call("get", "searcher:"..ARGV[1]..":session_id") or ""
    return {
        session_id,
        redis.call("get",   "session:"..session_id),
        redis.call("get",   "searcher:"..ARGV[1]..":search_character_id"),
        redis.call("hlen",  "searcher:"..ARGV[1]..":character"),
        redis.call("get",   "searcher:"..ARGV[1]..":style"),
        redis.call("scard", "searcher:"..ARGV[1]..":levels"),
    }""", 0, searcher_id)


def validate_searcher_is_searching(redis, searcher_id):
    """Check whether a searcher's mandatory keys are present and they're in the searchers set."""
    return redis.eval("""local session_id = redis.call("get", "searcher:"..ARGV[1]..":session_id") or ""
    return {
        redis.call("sismember", "searchers", ARGV[1]),
        session_id,
        redis.call("get",   "session:"..session_id),
        redis.call("get",   "searcher:"..ARGV[1]..":search_character_id"),
        redis.call("hlen",  "searcher:"..ARGV[1]..":character"),
        redis.call("get",   "searcher:"..ARGV[1]..":style"),
        redis.call("scard", "searcher:"..ARGV[1]..":levels"),
    }""", 0, searcher_id)


def refresh_searcher(redis, searcher_id):
    """Reset the expiry times on a searcher's keys."""
    return redis.eval("""local session_id = redis.call("get", "searcher:"..ARGV[1]..":session_id") or ""
    return {
        redis.call("get",       "session:"..session_id),
        redis.call("sismember", "searchers", ARGV[1]),
        redis.call("expire",    "searcher:"..ARGV[1]..":session_id",          30),
        redis.call("expire",    "searcher:"..ARGV[1]..":search_character_id", 30),
        redis.call("expire",    "searcher:"..ARGV[1]..":character",           30),
        redis.call("expire",    "searcher:"..ARGV[1]..":style",               30),
        redis.call("expire",    "searcher:"..ARGV[1]..":levels",              30),
        redis.call("expire",    "searcher:"..ARGV[1]..":filters",             30),
        redis.call("expire",    "searcher:"..ARGV[1]..":choices",             30),
    }""", 0, searcher_id)


searcher = namedtuple("searcher", ("id", "searching", "session_id", "user_id", "search_character_id", "character", "style", "levels", "filters", "choices"))


def fetch_searcher(redis, searcher_id):
    """Fetch searcher keys for matching."""
    searcher_keys = redis.eval("""local session_id = redis.call("get", "searcher:"..ARGV[1]..":session_id") or ""
    return {
        redis.call("sismember", "searchers", ARGV[1]),
        session_id,
        redis.call("get",      "session:"..session_id),
        redis.call("get",      "searcher:"..ARGV[1]..":search_character_id"),
        redis.call("hgetall",  "searcher:"..ARGV[1]..":character"),
        redis.call("get",      "searcher:"..ARGV[1]..":style"),
        redis.call("smembers", "searcher:"..ARGV[1]..":levels"),
        redis.call("lrange",   "searcher:"..ARGV[1]..":filters", 0, -1),
        redis.call("smembers", "searcher:"..ARGV[1]..":choices"),
    }""", 0, searcher_id)
    # Hashes and sets get returned as lists so we need to convert them manually.
    if searcher_keys[4]:
        searcher_keys[4] = {k: v for k, v in zip(*(iter(searcher_keys[4]),) * 2)}
    searcher_keys[6] = set(searcher_keys[6])
    searcher_keys[8] = set(searcher_keys[8])
    return searcher(searcher_id, *searcher_keys)


option_messages = {
    "script": "This is a script style chat.",
    "paragraph": "This is a paragraph style chat.",
    "sfw": "Please keep this chat safe for work.",
    "nsfw": "NSFW content is allowed.",
    "nsfw-extreme": "Extreme NSFW content is allowed.",
    "roulette": "TT: There is a 98.413% chance that you have just connected to someone anonymously. It seems that you should probably say \"Hello\" now.",
}

