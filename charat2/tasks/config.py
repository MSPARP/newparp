import os
from datetime import timedelta

# URLs
BROKER_URL = os.environ.get("CELERY_BROKER", "redis://localhost/1")

# Serialization
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

CELERY_DISABLE_RATE_LIMITS = True
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

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
