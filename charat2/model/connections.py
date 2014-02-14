from flask import g, request
from redis import ConnectionPool, StrictRedis
import os

from charat2.model import sm

# Pre- and post-request handlers for the main database connection.
# Also commit handler so we autocommit on successful requests.

def db_connect():
    g.db = sm()

def db_commit(response):
    g.db.commit()
    return response

def db_disconnect(response):
    g.db.close()
    del g.db
    return response

# Pre- and post-request handlers for the Redis connection.

redis_pool = ConnectionPool(host=os.environ['REDIS_HOST'], port=int(os.environ['REDIS_PORT']), db=int(os.environ['REDIS_DB']))

def redis_connect():
    g.redis = StrictRedis(connection_pool=redis_pool)

def redis_disconnect(response):
    del g.redis
    return response

