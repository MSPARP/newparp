import random

from tests import ParpTestCase

class BanTests(ParpTestCase):
    def ban(self, address: str, reason: str="Unittest ban."):
        with self.flask_client as client:
            # Login and poke the chat to get a valid cookie and a ChatUser entry.
            self.login(self.admin_user.username, "password", client=client)
            rv = client.post("/admin/ip_bans/new", data=dict(
                address=address,
                reason=reason
            ))
            assert rv.status_code in (200, 302)

    def random_ip(self) -> str:
        return ".".join([str(random.randint(1, 255)) for x in range(0, 4)])

    def test_no_bans(self):
        rv = self.flask_client.get("/", environ_base={
            "REMOTE_ADDR": "127.0.0.1"
        })

        assert rv.status_code == 200

    def test_user_ip_ban(self):
        ban_ip = self.random_ip()

        self.ban(ban_ip)

        rv = self.flask_client.get("/", environ_base={
            "REMOTE_ADDR": ban_ip
        })

        assert rv.status_code != 200
        assert b"pup-king-louie" in rv.data

    def test_admin_ip_ban(self):
        ban_ip = self.random_ip()

        with self.flask_client as client:
            # Login and poke the chat to get a valid cookie and a ChatUser entry.
            self.login(self.admin_user.username, "password", client=client)

            self.ban(ban_ip)

            rv = client.get("/", environ_base={
                "REMOTE_ADDR": ban_ip
            })

            assert rv.status_code == 200
            assert b"LOL UR IP BANNED" in rv.data

