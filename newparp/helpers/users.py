import json
import time

from datetime import datetime

from redis import StrictRedis

def queue_user_meta(context, redis: StrictRedis, last_ip: str):
    redis.hset("queue:usermeta", context.user.id, json.dumps({
        "type": "user",
        "last_online": time.mktime(datetime.now().timetuple()),
        "last_ip": last_ip,
    }))
