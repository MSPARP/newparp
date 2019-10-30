import datetime
import os

from kombu import Exchange, Queue

# Debug
if "DEBUG" in os.environ:
    worker_redirect_stdouts_level = "DEBUG"

# Broker and Result backends
broker_url = os.environ.get("CELERY_BROKER", "redis://localhost/1")
result_backend = os.environ.get("CELERY_RESULT", "redis://localhost/1")

# Time
timezone = "UTC"
result_expires = 3600  # 3600 seconds = 1 hour

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

    # Misc worker queue
    Queue("worker", Exchange("worker"), routing_key="worker", delivery_mode=1),

    # Matchmaker queue
    Queue("matchmaker", Exchange("matchmaker"), routing_key="matchmaker", delivery_mode=1),

    # Spamless queue
    Queue("spamless", Exchange("spamless"), routing_key="spamless", delivery_mode=1),
)

task_routes = {"newparp.tasks.spamless.CheckSpamTask": {"queue": "spamless"}}

# Beats config
beat_schedule = {
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
