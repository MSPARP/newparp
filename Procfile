web: gunicorn -b 0.0.0.0:5000 -k gevent -w 3 charat2:app
setup: python charat2/model/init_db.py
live: python charat2/workers/live.py
matchmaker: python charat2/workers/matchmaker.py
roulette_matchmaker: python charat2/workers/roulette_matchmaker.py
reaper: python charat2/workers/reaper.py
spamless: python charat2/workers/spamless.py

