#!/usr/bin/env python3

import os
import random
import subprocess
import sys
import time
import uuid

from redis import StrictRedis
from redis.exceptions import RedisError
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

from newparp.model import sm, SearchCharacterGroup
from newparp.model.connections import redis_pool


def init_db(redis: StrictRedis):
    print("Attempting to init database.")

    lock = str(uuid.uuid4())
    redis.setex("lock:initdb", 60, lock)

    time.sleep(random.uniform(1, 2))

    if redis.get("lock:initdb") == lock:
        print("Got the init lock, initating database.")
        subprocess.call(["python3", os.path.dirname(os.path.realpath(__file__)) + "/../newparp/model/init_db.py"])
    else:
        print("Didn't get the init lock, waiting 5 seconds.")
        time.sleep(5)


try:
    db = sm()
    redis = StrictRedis(connection_pool=redis_pool)

    # Redis online check.
    while True:
        try:
            redis.info()
            break
        except RedisError as e:
            print("Encountered a Redis error, waiting a second.")
            print(str(e))
            time.sleep(1)

    # Database online and initation check.
    while True:
        try:
            db.query(SearchCharacterGroup).first()
            break
        except (NoResultFound, ProgrammingError):
            init_db(redis)
            break
        except OperationalError as e:
            print("Encountered an OperationalError, waiting a second.")
            print(str(e))
            time.sleep(1)

finally:
    db.close()
    del db
    del redis

status = subprocess.call(sys.argv[1:])
sys.exit(status)
