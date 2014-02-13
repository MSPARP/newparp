main: gunicorn -b 0.0.0.0:8000 -k gevent -w 3 charat2:app
chat: gunicorn -b 0.0.0.0:8000 -k gevent -w 3 charat2.chat:app
setup: python setup.py develop && charat2_init_db