import sys

from charat2.chat import app

if "--debug" in sys.argv:
    app.debug=True

app.run()

