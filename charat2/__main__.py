import sys

from charat2 import app

if "--debug" in sys.argv:
    app.debug = True

app.run(threaded=True)

