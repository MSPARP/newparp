import os
from datetime import timedelta

from kombu import Exchange, Queue

# Debug
if 'DEBUG' in os.environ:
    CELERY_REDIRECT_STDOUTS_LEVEL = "DEBUG"

# Broker and Result backends
BROKER_URL = os.environ.get("CELERY_BROKER", "redis://localhost/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT", "redis://localhost/1")

# Time
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_TASK_RESULT_EXPIRES = 21600  # 21600 seconds = 6 hours

# Logging
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True

# Serialization
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Performance
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_DISABLE_RATE_LIMITS = True

# Queue config
CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
    # Default queue
    Queue('default', Exchange('default'), routing_key='default'),

    # Worker queue
    Queue('worker', Exchange('worker'), routing_key='worker', delivery_mode=1),
)

# Beats config
CELERYBEAT_SCHEDULE = {
    "generate_counters": {
        "task": "charat2.tasks.reaper.generate_counters",
        "schedule": timedelta(seconds=10),
    },
    "ping_longpolls": {
        "task": "charat2.tasks.reaper.ping_longpolls",
        "schedule": timedelta(seconds=5),
    },
    "reap": {
        "task": "charat2.tasks.reaper.reap",
        "schedule": timedelta(seconds=15),
    },
    "matchmaker": {
        "task": "charat2.tasks.matchmaker.run",
        "schedule": timedelta(seconds=10),
    },
    "roulette_matchmaker": {
        "task": "charat2.tasks.roulette_matchmaker.run",
        "schedule": timedelta(seconds=10),
    },
    "update_lastonline": {
        "task": "charat2.tasks.background.update_lastonline",
        "schedule": timedelta(seconds=15),
    }
}
