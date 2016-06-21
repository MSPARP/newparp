web: gunicorn -b 0.0.0.0:5000 -k gevent -w 3 newparp:app
setup: python3 newparp/model/init_db.py
migrate: alembic upgrade head
live: python3 newparp/workers/live.py
spamless: python3 newparp/workers/spamless.py
celery: celery -A newparp.tasks worker
celerybeat: celery -A newparp.tasks beat
