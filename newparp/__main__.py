import sys

from newparp import app

if "--debug" in sys.argv:
    app.debug = True

app.run(threaded=True)

