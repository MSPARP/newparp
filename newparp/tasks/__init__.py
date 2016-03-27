from celery import Celery, Task
from classtools import reify
from redis import StrictRedis

from newparp.model import sm
from newparp.model.connections import redis_pool

celery = Celery("newparp", include=[
    "newparp.tasks.background",
    "newparp.tasks.matchmaker",
    "newparp.tasks.reaper",
    "newparp.tasks.roulette_matchmaker",
])

celery.config_from_object('newparp.tasks.config')

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
