import json
import time

from sqlalchemy import func
from sqlalchemy.orm.session import Session

from newparp.model import IPBan
from newparp.model.connections import NewparpRedis


def queue_user_meta(context, redis: NewparpRedis, last_ip: str):
    redis.hset("queue:usermeta", "user:%s" % (context.user.id), json.dumps({
        "last_online": str(time.time()),
        "last_ip": last_ip,
    }))


def get_ip_banned(ip_address: str, db: Session, redis: NewparpRedis, use_cache: bool=True) -> bool:
    cached_bans = redis.get("bans:%s" % (ip_address))
    if cached_bans:
        try:
            return int(cached_bans) > 0
        except (ValueError, TypeError):
            pass

    ip_bans = db.query(func.count('*')).select_from(IPBan).filter(IPBan.address.op(">>=")(ip_address)).scalar()
    banned = ip_bans > 0
    redis.setex("bans:%s" % (ip_address), 60, ip_bans)

    return banned

