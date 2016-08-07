import time

from tests import ParpTestCase
from newparp.model import User
from newparp.helpers.users import queue_user_meta
from newparp.tasks.background import update_user_meta

class CeleryBackgroundTests(ParpTestCase):
    def check_valid_time(self, old: float, new: float):
        assert type(new) is float
        assert type(old) is float
        assert new != old
        assert new > old

    def test_user_meta_update_web(self):
        users = [self.create_user() for x in range(0, 8)]
        old_onlines = {}

        for user in users:
            with self.flask_client as client:
                old_onlines[user.id] = user.last_online.timestamp()
                self.login(user.username, "password", client=client)
                rv = client.get("/")
                assert rv.status_code == 200

        update_user_meta()
        self.db.expire_all()

        for uid, oldtime in old_onlines.items():
            updated = self.db.query(User).filter(User.id == uid).one()
            self.check_valid_time(oldtime, updated.last_online.timestamp())
