web: gunicorn -b 0.0.0.0:5000 -k gevent -w 3 charat2:app
setup: python charat2/model/init_db.py
migrate: alembic upgrade head
live: python charat2/workers/live.py
spamless: python charat2/workers/spamless.py
celery: celery -A charat2.tasks worker
celerybeat: celery -A charat2.tasks beat

