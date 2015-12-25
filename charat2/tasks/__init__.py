from celery import Celery, Task
from classtools import reify
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
    abstract = True

    @reify
    def db(self):
        return sm()

    @reify
    def redis(self):
        return StrictRedis(connection_pool=redis_pool)

    def after_return(self, *args, **kwargs):
        if hasattr(self, "db"):
            self.db.close()
            del self.db

        if hasattr(self, "redis"):
            del self.redis
