web: gunicorn -b 0.0.0.0:5000 -k gevent -w 3 charat2:app
setup: python charat2/model/init_db.py
reaper: python charat2/workers/reaper.py

