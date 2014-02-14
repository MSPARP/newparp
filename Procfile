main: gunicorn -b 0.0.0.0:8000 -k gevent -w 3 charat2:app
setup: python setup.py develop && python charat2/model/init_db.py

