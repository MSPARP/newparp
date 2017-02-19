import time

from newparp.model import User
from newparp.helpers.users import queue_user_meta
from newparp.tasks.background import update_user_meta
from tests import login, create_user

def check_valid_time(old: float, new: float):
    assert type(new) is float
    assert type(old) is float
    assert new != old
    assert new > old

def test_user_meta_update_web(db, app):
    users = [create_user(db) for x in range(0, 8)]
    old_onlines = {}

    for user in users:
        with app.test_client() as client:
            old_onlines[user.id] = user.last_online.timestamp()
            login(user.username, "password", client=client)
            rv = client.get("/")
            assert rv.status_code == 200

    update_user_meta()
    db.expire_all()

    for uid, oldtime in old_onlines.items():
        updated = db.query(User).filter(User.id == uid).one()
        check_valid_time(oldtime, updated.last_online.timestamp())
