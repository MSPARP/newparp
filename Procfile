web: gunicorn -b 0.0.0.0:5000 -k gevent -w 3 newparp:app
setup: python newparp/model/init_db.py
migrate: alembic upgrade head
live: python newparp/workers/live.py
spamless: python newparp/workers/spamless.py
celery: celery -A newparp.tasks worker
celerybeat: celery -A newparp.tasks beat

