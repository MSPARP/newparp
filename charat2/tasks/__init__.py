from celery import Celery, Task
from redis import StrictRedis

from charat2.model import sm
from charat2.model.connections import redis_pool

celery = Celery("newparp", include=[
    "charat2.tasks.background",
    "charat2.tasks.matchmaker",
    "charat2.tasks.reaper",
    "charat2.tasks.roulette_matchmaker",
])

celery.config_from_object('charat2.tasks.config')

class WorkerTask(Task):
    abstrct = True
    _db = None
    _redis = None

    @property
    def db(self):
        if self._db is None:
            self._db = sm()

        return self._db

    @property
    def redis(self):
        if self._redis is None:
            self._redis = StrictRedis(connection_pool=redis_pool)

        return self._redis
