# import datetime
# import json
# import urllib.parse
# import html
#
# from newparp.model import Message
# from tests import ParpTestCase
#
# class GroupTests(ParpTestCase):
#     def test_send_messages(self):
#         with self.flask_client as client:
#             # Login and poke the chat to get a valid cookie and a ChatUser entry.
#             self.login(self.normal_user.username, "password", client=client)
#             client.get("/" + self.group_chat.url)
#
#             for msgtype in Message.type.property.columns[0].type.enums:
#                 rv = client.post("/chat_api/send", data={
#                     "chat_id": self.group_chat.id,
#                     "type": msgtype,
#                     "text": "This is a unit test message sent on [i]%s[/i]. Type: %s" % (
#                         str(datetime.datetime.now()),
#                         msgtype
#                     ),
#                 })
#                 assert rv.status_code == 204
#
#     def test_set_topic(self):
#         topics = [
#             "Unit testing topic created on %s" % (str(datetime.datetime.now())),
#             "test overflow cutoff " * 100,
#             ""
#         ]
#
#         # Moderator abilities
#         with self.flask_client as client:
#             # Login and poke the chat to get a valid cookie and a ChatUser entry.
#             self.login(self.admin_user.username, "password", client=client)
#             client.get("/" + self.group_chat.url)
#
#             for topic in topics:
#                 # Test if the topic is able to be set on the server side.
#                 rv = client.post("/chat_api/set_topic", data={
#                     "chat_id": self.group_chat.id,
#                     "topic": topic
#                 })
#                 print(rv.data)
#                 assert rv.status_code == 204
#
#                 # Test if the topic is set and displaying in the chat metadata.
#                 rv = client.get("/" + self.group_chat.url + ".json")
#                 data = json.loads(rv.data.decode("utf8"))
#                 assert data["chat"]["topic"] == topic[:500]
#
#         with self.flask_client as client:
#             # Login and poke the chat to get a valid cookie and a ChatUser entry.
#             self.login(self.normal_user.username, "password", client=client)
#             client.get("/" + self.group_chat.url)
#
#             rv = client.post("/chat_api/set_topic", data={
#                 "chat_id": self.group_chat.id,
#                 "topic": "fail"
#             })
#             assert rv.status_code == 403
#

