import os
from datetime import timedelta

from kombu import Exchange, Queue

# Debug
if "DEBUG" in os.environ:
    worker_redirect_stdouts_level = "DEBUG"

# Broker and Result backends
broker_url = os.environ.get("CELERY_BROKER", "redis://localhost/1")
result_backend = os.environ.get("CELERY_RESULT", "redis://localhost/1")

# Time
timezone = "UTC"
result_expires = 21600  # 21600 seconds = 6 hours

# Logging
task_store_errors_even_if_ignored = True

# Serialization
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Performance
worker_disable_rate_limits = True

# Queue config
task_default_queue = "default"
task_queues = (
    # Default queue
    Queue("default", Exchange("default"), routing_key="default"),

    # Worker queue
    Queue("worker", Exchange("worker"), routing_key="worker", delivery_mode=1),

    # Matchmaker queue
    Queue("matchmaker", Exchange("matchmaker"), routing_key="matchmaker", delivery_mode=1),
)

# Beats config
beat_schedule = {
    "generate_counters": {
        "task": "newparp.tasks.background.generate_counters",
        "schedule": timedelta(seconds=10),
    },
    "unlist_chats": {
        "task": "newparp.tasks.background.unlist_chats",
        "schedule": timedelta(hours=12),
    },
    "update_lastonline": {
        "task": "newparp.tasks.background.update_lastonline",
        "schedule": timedelta(seconds=5),
    },
    "update_user_meta": {
        "task": "newparp.tasks.background.update_user_meta",
        "schedule": timedelta(seconds=5),
    },
    "generate_searching_counter": {
        "task": "newparp.tasks.matchmaker.generate_searching_counter",
        "schedule": timedelta(seconds=10),
    },
    "ping_longpolls": {
        "task": "newparp.tasks.reaper.ping_longpolls",
        "schedule": timedelta(seconds=5),
    },
    "reap": {
        "task": "newparp.tasks.reaper.reap",
        "schedule": timedelta(seconds=1),
    },
}
