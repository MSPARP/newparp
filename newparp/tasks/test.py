from newparp.model import SearchCharacter
from newparp.model.connections import session_scope
from newparp.tasks import celery, WorkerTask


@celery.task(base=WorkerTask, queue="test")
def no_test():
    pass


@celery.task(base=WorkerTask, queue="test")
def redis_test():
    redis_test.redis.set("health", 1)


@celery.task(base=WorkerTask, queue="test")
def postgres_test():
    with session_scope() as db:
        db.query(SearchCharacter).first()

