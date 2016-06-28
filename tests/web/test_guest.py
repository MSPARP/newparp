import time

from tests import ParpTestCase

class GuestTests(ParpTestCase):
    def test_front_200(self):
        rv = self.flask_client.get("/")
        assert rv.status_code == 200

    def test_ok_health(self):
        rv = self.flask_client.get("/health")
        assert b"ok" in rv.data

    def test_guest_redirect(self):
        rv = self.flask_client.get("/" + self.group_chat.url)
        assert b"You need to register or log in before you can join this chat" in rv.data

    def test_guest_can_log(self):
        rv = self.flask_client.get("/" + self.group_chat.url + "/log")
        assert rv.status_code == 200

    # def test_no_412_dots(self):
    #     rv = self.flask_client.get("/breaking.butts")
    #     assert rv.status_code != 412

    def test_nonexistant_log_404(self):
        rv = self.flask_client.get("/" + str(int(time.time())))
        assert rv.status_code == 404
