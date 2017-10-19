import datetime
import os

from kombu import Exchange, Queue

# Debug
if "DEBUG" in os.environ:
    CELERY_REDIRECT_STDOUTS_LEVEL = "DEBUG"

# Broker and Result backends
BROKER_URL = os.environ.get("CELERY_BROKER", "redis://localhost/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT", "redis://localhost/1")

# Time
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_TASK_RESULT_EXPIRES = 3600  # 3600 seconds = 1 hour

# Logging
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True

# Serialization
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Performance
CELERY_DISABLE_RATE_LIMITS = True

# Queue config
CELERY_DEFAULT_QUEUE = "default"
CELERY_QUEUES = (
    # Default queue
    Queue("default", Exchange("default"), routing_key="default"),

    # Misc worker queue
    Queue("worker", Exchange("worker"), routing_key="worker", delivery_mode=1),

    # Matchmaker queue
    Queue("matchmaker", Exchange("matchmaker"), routing_key="matchmaker", delivery_mode=1),

    # Spamless queue
    Queue("spamless", Exchange("spamless"), routing_key="spamless", delivery_mode=1),
)

CELERY_ROUTES = {"newparp.tasks.spamless.CheckSpamTask": {"queue": "spamless"}}

# Beats config
CELERYBEAT_SCHEDULE = {
    "generate_counters": {
        "task": "newparp.tasks.background.generate_counters",
        "schedule": datetime.timedelta(seconds=30),
    },
    "unlist_chats": {
        "task": "newparp.tasks.background.unlist_chats",
        "schedule": datetime.timedelta(hours=12),
    },
    "update_lastonline": {
        "task": "newparp.tasks.background.update_lastonline",
        "schedule": datetime.timedelta(seconds=10),
    },
    "update_user_meta": {
        "task": "newparp.tasks.background.update_user_meta",
        "schedule": datetime.timedelta(seconds=10),
    },
    "generate_searching_counter": {
        "task": "newparp.tasks.matchmaker.generate_searching_counter",
        "schedule": datetime.timedelta(seconds=10),
    },
    "reap": {
        "task": "newparp.tasks.reaper.reap",
        "schedule": datetime.timedelta(seconds=60),
    },
}
