from flask import abort, Flask, g, request
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from charat2.auth import get_request_user, set_cookie
from charat2.model import User, AnyChat, UserChat
from charat2.model.connections import (
    db_connect,
    db_commit,
    db_disconnect,
    redis_connect,
    redis_disconnect,
)

app = Flask(__name__)

def get_user_chat():
    # Fetch User, Chat and UserChat objects.
    # They must already exist (ie. we must have logged in and hit the chat
    # page before requesting anything from this app).
    if request.method!="POST":
        abort(405)
    if "session" not in request.cookies:
        abort(400)
    user_id = g.redis.get("session:" + request.cookies["session"])
    if user_id is None:
        abort(400)
    print user_id
    if "chat_id" not in request.form:
        abort(400)
    try:
        g.user_chat, g.user, g.chat = g.db.query(
            UserChat, User, AnyChat,
        ).join(
            User, UserChat.user_id==User.id,
        ).join(
            AnyChat, UserChat.chat_id==AnyChat.id,
        ).filter(and_(
            UserChat.user_id==user_id,
            UserChat.chat_id==request.form["chat_id"],
        )).one()
    except NoResultFound:
        abort(400)

app.before_request(redis_connect)
app.before_request(db_connect)
app.before_request(get_user_chat)

app.after_request(db_commit)

app.teardown_request(db_disconnect)
app.teardown_request(redis_disconnect)

@app.route('/messages')
def messages():
    raise NotImplementedError

@app.route('/send')
def send():
    raise NotImplementedError

@app.route('/set_state')
def set_state():
    raise NotImplementedError

@app.route('/set_group')
def set_group():
    raise NotImplementedError

@app.route('/user_action')
def user_action():
    raise NotImplementedError

@app.route('/set_flag')
def set_flag():
    raise NotImplementedError

@app.route('/set_topic')
def set_topic():
    raise NotImplementedError

@app.route('/save')
def save():
    raise NotImplementedError

@app.route('/ping')
def ping():
    raise NotImplementedError

@app.route('/quit')
def quit():
    raise NotImplementedError

